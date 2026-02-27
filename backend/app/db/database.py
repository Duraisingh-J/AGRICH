"""Async SQLAlchemy database configuration and dependencies."""

from collections.abc import AsyncGenerator
import ssl

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy models."""


settings = get_settings()
database_url_normalized = settings.database_url.lower()

# Proper Neon SSL handling
connect_args: dict = {}

if "sslmode=require" in database_url_normalized or "neon.tech" in database_url_normalized:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False  # important for Neon on some hosts
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    connect_args["ssl"] = ssl_context

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,   # helps with Neon connections
    connect_args=connect_args,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session for request scope."""
    async with SessionLocal() as session:
        yield session