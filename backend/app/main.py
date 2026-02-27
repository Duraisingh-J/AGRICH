"""FastAPI entrypoint for AGRICHAIN backend."""

import contextvars
import json
import logging
import time
import uuid
import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.batch import router as batch_router
from app.api.qr import router as qr_router
from app.config import get_settings
from app.db.database import SessionLocal, engine
from app.services.blockchain_service import BlockchainService
from app.services.cache_service import CacheService
from app.services.ipfs_service import IPFSService
from app.workers.blockchain_listener import (
    get_event_backlog_size,
    get_last_processed_block,
    get_listener,
    get_listener_uptime,
)

correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="-")


class CorrelationIdFilter(logging.Filter):
    """Inject correlation IDs into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_var.get()
        return True


class JsonLogFormatter(logging.Formatter):
    """JSON log formatter for production logging option."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "-"),
        }
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure structured logging for the service."""

    settings = get_settings()
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.app_log_level))

    formatter: logging.Formatter
    if settings.log_json:
        formatter = JsonLogFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(correlation_id)s | %(message)s"
        )

    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            handler.setFormatter(formatter)

    for handler in root_logger.handlers:
        has_filter = any(isinstance(existing_filter, CorrelationIdFilter) for existing_filter in handler.filters)
        if not has_filter:
            handler.addFilter(CorrelationIdFilter())


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Application lifecycle handler."""

    settings = get_settings()
    configure_logging()
    logger = logging.getLogger("app.lifecycle")
    listener_task = None

    if settings.enable_blockchain_listener:
        listener = get_listener(settings.blockchain_poll_interval)
        if not listener.is_running:
            listener_task = asyncio.create_task(listener.start())
            logger.info("Blockchain listener background task started")

    logger.info("Starting AGRICHAIN backend")
    try:
        yield
    finally:
        if settings.enable_blockchain_listener:
            listener = get_listener(settings.blockchain_poll_interval)
            await listener.stop()
            if listener_task is not None:
                await listener_task
            logger.info("Blockchain listener shutdown complete")
        await engine.dispose()
        logger.info("Shutting down AGRICHAIN backend")


def create_app() -> FastAPI:
    """Create and configure FastAPI app instance."""

    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(batch_router, prefix=settings.api_prefix)
    app.include_router(qr_router, prefix=settings.api_prefix)

    blockchain_service = BlockchainService()
    cache_service = CacheService()
    ipfs_service = IPFSService()

    @app.middleware("http")
    async def correlation_id_middleware(request: Request, call_next):
        """Attach correlation ID to request context and response headers."""

        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
        token = correlation_id_var.set(correlation_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
            response.headers["x-correlation-id"] = correlation_id
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logging.getLogger("app.http").info(
                "request.completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            correlation_id_var.reset(token)

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        """Service liveness endpoint."""

        return {"status": "ok"}

    @app.get("/system/health/deep", tags=["system"])
    async def deep_health_check() -> dict[str, Any]:
        """Detailed health checks for database, blockchain, Redis, and IPFS."""

        database_healthy = False
        try:
            async with SessionLocal() as session:
                await session.execute(text("SELECT 1"))
                database_healthy = True
        except Exception:
            logging.getLogger("app.health").exception("Database health check failed")

        blockchain_healthy = await blockchain_service.is_blockchain_healthy()
        redis_healthy = await cache_service.is_healthy()
        ipfs_healthy = await ipfs_service.is_healthy()

        listener = get_listener(settings.blockchain_poll_interval)
        backlog_size = await get_event_backlog_size()
        last_block = await get_last_processed_block()

        services = {
            "database": {"healthy": database_healthy},
            "blockchain": {"healthy": blockchain_healthy},
            "redis": {"healthy": redis_healthy},
            "ipfs": {"healthy": ipfs_healthy},
            "listener": {
                "running": listener.is_running,
                "backlog_size": backlog_size,
                "last_block": last_block,
                "uptime_seconds": get_listener_uptime(),
            },
        }
        overall = all(item.get("healthy", True) for item in services.values())

        return {
            "status": "ok" if overall else "degraded",
            "services": services,
        }

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        """Handle known HTTP exceptions consistently."""

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle request validation errors."""

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        """Fallback exception handler to avoid leaking internals."""

        logging.getLogger("app.errors").exception("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    return app


app: FastAPI = create_app()
