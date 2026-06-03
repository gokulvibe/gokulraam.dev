"""Tiny schema migrator. Idempotent. Dialect-aware (SQLite + Postgres).

SQLAlchemy `Base.metadata.create_all()` creates *missing tables* but never
adds new columns to existing ones. For our hobby-scale workflow we don't
need Alembic — we just drop occasional `ALTER TABLE ADD COLUMN` entries
into _COLUMN_ADDS and they run on every startup, silently no-op-ing when
the column is already present.

Column-lookup uses SQLAlchemy's Inspector (dialect-neutral). DDL fragments
are written for SQLite and translated for Postgres at emission time.

When this file grows past ~10 entries, switch to Alembic.
"""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.db import engine


# (table_name, column_name, column_sql). The column_sql is written in
# "SQLite dialect" and translated to other dialects by _translate_ddl().
_COLUMN_ADDS: list[tuple[str, str, str]] = [
    # Phase D — badminton scraper
    ("badminton_tournaments", "start_date", "DATETIME"),
    ("badminton_tournaments", "end_date", "DATETIME"),
    ("badminton_tournaments", "source_url", "VARCHAR(400) DEFAULT ''"),
    # Light theme — casual bio + interests
    ("profile", "casual_about", "TEXT DEFAULT ''"),
    ("profile", "casual_interests", "VARCHAR(300) DEFAULT ''"),
    # Analytics — flag self-views so they don't pollute the stats
    ("page_views", "is_admin", "BOOLEAN DEFAULT 0"),
    # /now categorized — group items into building/reading/watching/etc.
    ("now_items", "kind", "VARCHAR(40) DEFAULT ''"),
]


# Per-dialect DDL substitutions. SQLite types are advisory so we keep
# the source DDL in SQLite form; Postgres needs proper substitutions.
_DIALECT_MAP: dict[str, list[tuple[str, str]]] = {
    "postgresql": [
        ("DATETIME", "TIMESTAMP"),
        ("BOOLEAN DEFAULT 0", "BOOLEAN DEFAULT FALSE"),
        ("BOOLEAN DEFAULT 1", "BOOLEAN DEFAULT TRUE"),
    ],
    "sqlite": [],
}


def _translate_ddl(ddl: str, dialect: str) -> str:
    for old, new in _DIALECT_MAP.get(dialect, []):
        ddl = ddl.replace(old, new)
    return ddl


def _existing_columns(conn, table: str) -> set[str] | None:
    """Returns the set of existing column names for `table`, or None if the
    table doesn't exist yet (in which case create_all() will produce it with
    every column already in place — nothing for us to migrate)."""
    insp = inspect(conn)
    if not insp.has_table(table):
        return None
    return {col["name"] for col in insp.get_columns(table)}


def run_migrations() -> int:
    """Returns number of columns added this run."""
    added = 0
    with engine.begin() as conn:
        dialect = conn.dialect.name
        for table, column, ddl in _COLUMN_ADDS:
            cols = _existing_columns(conn, table)
            if cols is None:
                continue  # table not created yet — model defs cover it
            if column in cols:
                continue
            ddl_final = _translate_ddl(ddl, dialect)
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_final}"))
            added += 1
    return added


# ─── Data backfills (idempotent UPDATEs) ────────────────────
#
# When the seed defaults change after the table is already populated,
# new defaults don't take effect on existing rows (seeds are
# insert-if-missing, not upsert). Use this list to push *targeted*
# updates: a row is only modified when EVERY column in `where` matches
# its old value exactly — so an entry the user has already edited is
# never trampled.
#
# Schema:
#   { "table": "uses_items",
#     "where": {"slug": "keyboard", "name": "— keyboard"},
#     "set":   {"name": "Keychron K3", "note": "low-profile · mac layout"} }
#
# Once a backfill applies it can never re-fire: the `where` clause is
# the *old* value, which no longer exists in the row after the UPDATE.
# Safe to leave entries in the list forever.

_DataBackfill = dict[str, "str | dict[str, str]"]

_DATA_BACKFILLS: list[_DataBackfill] = [
    # entries land here as content drafts are merged.
]


def run_data_backfills() -> int:
    """Returns number of rows updated this run (across all backfills)."""
    total = 0
    with engine.begin() as conn:
        for bf in _DATA_BACKFILLS:
            table = bf.get("table")
            where = bf.get("where") or {}
            set_ = bf.get("set") or {}
            if not (isinstance(table, str) and isinstance(where, dict) and isinstance(set_, dict)):
                continue
            if not where or not set_:
                continue
            # Skip if the table doesn't exist (e.g. on a fresh DB where
            # create_all hasn't fired yet — shouldn't happen given call
            # order in main.py, but defensive).
            if _existing_columns(conn, table) is None:
                continue
            where_sql = " AND ".join(f"{c} = :w_{c}" for c in where)
            set_sql = ", ".join(f"{c} = :s_{c}" for c in set_)
            params = {**{f"w_{c}": v for c, v in where.items()},
                      **{f"s_{c}": v for c, v in set_.items()}}
            result = conn.execute(
                text(f"UPDATE {table} SET {set_sql} WHERE {where_sql}"),
                params,
            )
            total += result.rowcount or 0
    return total
