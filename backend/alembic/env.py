"""Alembic env, wired to app.config and app.models.

DATABASE_URL comes from `app.config.get_settings().database_url` so we
honor the same env var the rest of the app reads (SQLite locally,
Neon Postgres in prod). target_metadata is `app.db.Base.metadata` so
`alembic revision --autogenerate` can diff the live models.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make `app.*` importable when alembic runs from backend/
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import get_settings   # noqa: E402
from app.db import Base               # noqa: E402
import app.models  # noqa: F401,E402  (registers tables on Base.metadata)


config = context.config

# Use app settings for the URL — overrides whatever's in alembic.ini.
config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection — produces SQL."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        # SQLite needs batch mode for most ALTER TABLE operations
        # (Alembic emulates them by recreating the table). Harmless
        # on Postgres but we keep it off there to skip the extra work.
        is_sqlite = connection.dialect.name == "sqlite"
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=is_sqlite,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
