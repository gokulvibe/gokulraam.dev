"""Database migration runner — Alembic-backed.

Replaces the previous bespoke ALTER TABLE list. Run this *before*
uvicorn (as part of deploy / `make migrate`), not from the FastAPI
lifespan. The server no longer mutates the DB on boot.

Usage:
  cd backend && .venv/bin/python -m app.migrate

What it does, by current DB state:

  • Fresh DB (no app tables, no alembic_version)
      `alembic upgrade head` runs the baseline migration which calls
      Base.metadata.create_all + every revision since. Tables created.

  • Existing populated DB without alembic_version (legacy production
    + pre-Alembic local SQLite — the case that triggered the switch)
      `alembic stamp head` records the baseline as already applied.
      The schema is at head; we just teach Alembic that fact. No DDL.

  • Alembic-managed DB (alembic_version exists)
      `alembic upgrade head` applies any pending revisions. No-op if
      already up to date.

Idempotent. Safe to run repeatedly.
"""

from __future__ import annotations

import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.db import engine


_ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"

# Tables we own. If at least one exists, the DB is "populated" — i.e.
# the schema was created before Alembic took over. We stamp instead of
# running the baseline create_all (which would error on duplicates).
_KNOWN_APP_TABLES = {
    "til_posts", "profile", "now_items", "uses_items",
    "badminton_players", "badminton_tournaments",
    "work_roles", "projects", "museum_exhibits",
    "photos", "guestbook_entries", "logbook_entries",
}


def _alembic_cfg() -> Config:
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("script_location", str(_ALEMBIC_INI.parent / "alembic"))
    return cfg


def _existing_tables() -> set[str]:
    return set(inspect(engine).get_table_names())


def main() -> int:
    tables = _existing_tables()
    has_alembic = "alembic_version" in tables
    has_app_tables = bool(_KNOWN_APP_TABLES & tables)
    cfg = _alembic_cfg()

    if not has_alembic and has_app_tables:
        # Legacy populated DB — schema already at head. Don't run the
        # baseline create_all (it'd hit "table already exists"). Just
        # record that we're at head.
        print("[migrate] populated DB without alembic_version · stamping head (no DDL)")
        command.stamp(cfg, "head")
        print("[migrate] done")
        return 0

    # Fresh DB or Alembic-managed DB: upgrade head does the right thing.
    # On a fresh DB, the baseline migration's upgrade() calls
    # Base.metadata.create_all to bootstrap every table.
    print("[migrate] running alembic upgrade head")
    command.upgrade(cfg, "head")
    print("[migrate] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
