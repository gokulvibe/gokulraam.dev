"""baseline — schema as-of 2026-06-06 (the day we switched to Alembic).

Strategy: instead of redeclaring every table with op.create_table() in
this file, we let SQLAlchemy do it via `Base.metadata.create_all`. The
models are the canonical source. This file's job is just to record
"the baseline schema has been applied".

Reconciliation by environment (driven by app.migrate at run time):

  • Fresh DB
      `alembic upgrade head` runs this upgrade(); it calls create_all()
      against the bound connection → every model's table is created.
      Subsequent revisions then apply on top.

  • Existing populated DB (our production Postgres on Neon, plus the
    pre-Alembic local SQLite)
      app.migrate detects there's no alembic_version row but there ARE
      app tables, and stamps this revision instead of running it. The
      schema is already at head; we just teach Alembic that fact.

Past additive changes from the old `app/migrate._COLUMN_ADDS` list
(now_items.kind, profile.casual_*, page_views.is_admin,
badminton_tournaments.start_date/end_date/source_url) are all part of
the live model definitions, so create_all() includes them in the
baseline. Nothing to re-codify.

Revision ID: 20260606_baseline
Revises:
Create Date: 2026-06-06
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260606_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create every table currently declared on Base.metadata."""
    # Import here so the module loads even if alembic is run with a
    # version of the code where app.models doesn't import cleanly
    # (defensive — should never happen, but failing fast in env.py is
    # better than failing inside a migration mid-transaction).
    from app.db import Base
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    """Drop every table currently declared on Base.metadata."""
    from app.db import Base
    Base.metadata.drop_all(bind=op.get_bind())
