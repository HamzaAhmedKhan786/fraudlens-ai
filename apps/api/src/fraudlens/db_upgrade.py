"""Upgrade both Alembic-managed and legacy local FraudLens databases safely."""

import sqlite3
from pathlib import Path

from alembic import command
from alembic.config import Config

from fraudlens.config import get_settings


def _sqlite_path(url: str) -> Path | None:
    prefix = "sqlite+aiosqlite:///"
    return Path(url.removeprefix(prefix)).resolve() if url.startswith(prefix) else None


def main() -> None:
    settings = get_settings()
    config = Config("apps/api/alembic.ini")
    config.set_main_option("sqlalchemy.url", settings.database_url)
    path = _sqlite_path(settings.database_url)
    if path and path.exists():
        with sqlite3.connect(path) as connection:
            tables = {
                row[0]
                for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
        if "cases" in tables and "alembic_version" not in tables:
            # Legacy development databases were created with metadata.create_all().
            # Stamp only the schema that can be proven by table presence, then migrate forward.
            command.stamp(config, "20260812_0002" if "uploads" in tables else "20260810_0001")
    command.upgrade(config, "head")


if __name__ == "__main__":
    main()
