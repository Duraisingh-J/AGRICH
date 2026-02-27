"""Programmatic migration runner for initializing database schema."""

from __future__ import annotations

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.config import get_settings


async def run_migrations() -> None:
    """Run Alembic migrations to head for current environment."""

    project_root = Path(__file__).resolve().parents[1]
    alembic_ini = project_root / "alembic.ini"

    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(project_root / "db" / "migrations"))
    config.set_main_option("sqlalchemy.url", get_settings().database_url)

    await asyncio.to_thread(command.upgrade, config, "head")


if __name__ == "__main__":
    asyncio.run(run_migrations())
