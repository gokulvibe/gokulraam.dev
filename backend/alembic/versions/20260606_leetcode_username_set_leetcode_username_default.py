"""set leetcode username default

Sets `leetcode_stats.username` to 'gokulraamofficial' on the
singleton row IF the row still holds the empty default. Guarded so
existing edits never get trampled — an admin who's already pointed
the integration at a different LeetCode handle keeps that handle.

Idempotent: after this fires once, the WHERE no longer matches, so
re-runs are no-ops.

Revision ID: 20260606_leetcode_username
Revises: 004444fa7785
Create Date: 2026-06-06
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "20260606_leetcode_username"
down_revision: Union[str, None] = "004444fa7785"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_DEFAULT_USERNAME = "gokulraamofficial"


def upgrade() -> None:
    op.execute(
        text(
            "UPDATE leetcode_stats SET username = :u "
            "WHERE id = 1 AND (username IS NULL OR username = '')"
        ).bindparams(u=_DEFAULT_USERNAME)
    )


def downgrade() -> None:
    # Reverse: only clear the username if it's still ours and never
    # been changed by an admin. Keeps any subsequent edit safe.
    op.execute(
        text(
            "UPDATE leetcode_stats SET username = '' "
            "WHERE id = 1 AND username = :u"
        ).bindparams(u=_DEFAULT_USERNAME)
    )
