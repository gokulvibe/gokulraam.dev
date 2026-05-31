"""Tiny schema migrator. Idempotent.

SQLAlchemy `Base.metadata.create_all()` creates *missing tables* but never
adds new columns to existing ones. For our hobby-scale SQLite workflow we
don't need Alembic — we just need a place to drop occasional `ALTER TABLE
ADD COLUMN` statements that run on every startup and silently no-op when the
column already exists.

When this file grows past ~10 entries, switch to Alembic.
"""

from __future__ import annotations

from sqlalchemy import text

from app.db import engine


# (table_name, column_name, column_sql)
_COLUMN_ADDS: list[tuple[str, str, str]] = [
    # Phase D — badminton scraper
    ("badminton_tournaments", "start_date", "DATETIME"),
    ("badminton_tournaments", "end_date", "DATETIME"),
    ("badminton_tournaments", "source_url", "VARCHAR(400) DEFAULT ''"),
]


def _existing_columns(conn, table: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {r[1] for r in rows}


def run_migrations() -> int:
    """Returns number of columns added this run."""
    added = 0
    with engine.begin() as conn:
        for table, column, ddl in _COLUMN_ADDS:
            try:
                cols = _existing_columns(conn, table)
            except Exception:  # noqa: BLE001
                # Table doesn't exist yet — Base.metadata.create_all() will
                # create it with the column already in place.
                continue
            if column in cols:
                continue
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
            added += 1
    return added
