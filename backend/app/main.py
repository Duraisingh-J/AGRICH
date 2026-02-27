"""FastAPI entrypoint for AGRICHAIN backend."""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.config import get_settings
from app.db.database import engine


def configure_logging() -> None:
    """Configure structured logging for the service."""

    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.app_log_level),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Application lifecycle handler."""

    configure_logging()
    logger = logging.getLogger("app.lifecycle")
    logger.info("Starting AGRICHAIN backend")
    try:
        yield
    finally:
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

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        """Service liveness endpoint."""

        return {"status": "ok"}

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
