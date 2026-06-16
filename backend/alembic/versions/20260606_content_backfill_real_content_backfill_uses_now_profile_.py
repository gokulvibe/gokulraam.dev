"""real content backfill (now · profile · museum)

Revision ID: 20260606_content_backfill
Revises: 58ef8fbb9c48
Create Date: 2026-06-06 19:38:06.509619

Replaces seeded placeholders with real content drawn from the owner.

Every UPDATE is guarded against the exact original default text — if the
row has been admin-edited at all, the WHERE no longer matches and the
update is a no-op.

Originally also touched uses_items, but the /uses section has since been
removed from the site, so those operations were dropped.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260606_content_backfill'
down_revision: Union[str, None] = '58ef8fbb9c48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --- old defaults (must match seed.py exactly) ---

_OLD_CASUAL_ABOUT = (
    "I work as a software engineer at Saama in Coimbatore, where we build "
    "tools for clinical research. Outside work, you'll usually find me on a "
    "badminton court, in the gym, or with a book."
)
_OLD_CASUAL_INTERESTS = "Badminton, Fitness, Reading, Music"

_OLD_LISTENING = "lo-fi loops + ambient. whatever ships code."

_OLD_COMING_OF_AGE = (
    "Replace this with what college was like — late nights, the first big project, the "
    "friends you kept, the ones you lost. The moment code clicked. NaviGuide was here.\n\n"
    "Photos from that time go a long way."
)
_OLD_THE_COURT = (
    "Replace this with your court story — when you started, the players you watch, the time "
    "you actually beat someone better than you, the time you didn't. The backhand you've been "
    "chasing for two years.\n\n"
    "Action shot would land beautifully here."
)
_OLD_THE_WORKSHOP = (
    "Replace this with whatever's currently lighting you up — a project, a book, a person, "
    "a question you can't put down. The 'now', but more honest than the public /now page.\n\n"
    "This room can change as often as you like."
)


# --- new content ---

_NEW_CASUAL_ABOUT = (
    "I work as a software engineer at Saama in Coimbatore, building tools for "
    "clinical research. Wired ADHD-style — short loops, music on, ten tabs "
    "open, coffee never too far away. Outside work I'm on a badminton court "
    "most weekends, in the gym on weekdays, and friendly to a fault if you "
    "say hi."
)
_NEW_CASUAL_INTERESTS = "Badminton, Lifting, Pop music, Marvel"

_NEW_LISTENING = "pop on repeat. one direction · taylor · weeknd. while shipping code."

_NEW_COMING_OF_AGE = (
    "Kumaraguru, four years. NaviGuide was the first project that taught me the "
    "right abstraction makes the next ten features cheap. Late nights in the lab, "
    "Dhoni on every dorm TV when India was playing. The moment code clicked: when "
    "I deleted ten lines and the same thing kept working."
)
_NEW_THE_COURT = (
    "Saturdays and Sundays without fail — gym shorts, racquet sleeve, court 3 if "
    "I'm lucky. Lakshya's footwork, Lee Zii Jia's smash, Shi Yu Qi's calm. The "
    "Apacs Z-Ziggler Reborn strung tight, frame heavy through the shot. The "
    "backhand drop is still a work in progress two years in."
)
_NEW_THE_WORKSHOP = (
    "Two ear-buds in, pop on rotation — One Direction and Taylor on heavy days, "
    "Weeknd when the algorithm gets melancholic. The frother whines in the "
    "kitchen — sometimes a coffee, sometimes a whey shake — and either way "
    "it ends up lukewarm beside the keyboard. The current obsession is making "
    "backend APIs that read like they had only one author. SOLID isn't a "
    "religion but it's an aesthetic. Caches, queues, query plans. Lifting on "
    "weekdays — almost two years in, still chasing the build."
)


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text("UPDATE profile SET casual_about = :new WHERE id = 1 AND casual_about = :old"),
        {"new": _NEW_CASUAL_ABOUT, "old": _OLD_CASUAL_ABOUT},
    )
    conn.execute(
        sa.text("UPDATE profile SET casual_interests = :new WHERE id = 1 AND casual_interests = :old"),
        {"new": _NEW_CASUAL_INTERESTS, "old": _OLD_CASUAL_INTERESTS},
    )

    conn.execute(
        sa.text("UPDATE now_items SET value = :new WHERE slug = 'listening' AND value = :old"),
        {"new": _NEW_LISTENING, "old": _OLD_LISTENING},
    )

    conn.execute(
        sa.text("UPDATE museum_exhibits SET body_md = :new WHERE slug = 'coming-of-age' AND body_md = :old"),
        {"new": _NEW_COMING_OF_AGE, "old": _OLD_COMING_OF_AGE},
    )
    conn.execute(
        sa.text("UPDATE museum_exhibits SET body_md = :new WHERE slug = 'the-court' AND body_md = :old"),
        {"new": _NEW_THE_COURT, "old": _OLD_THE_COURT},
    )
    conn.execute(
        sa.text("UPDATE museum_exhibits SET body_md = :new WHERE slug = 'the-workshop' AND body_md = :old"),
        {"new": _NEW_THE_WORKSHOP, "old": _OLD_THE_WORKSHOP},
    )


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(
        sa.text("UPDATE profile SET casual_about = :old WHERE id = 1 AND casual_about = :new"),
        {"new": _NEW_CASUAL_ABOUT, "old": _OLD_CASUAL_ABOUT},
    )
    conn.execute(
        sa.text("UPDATE profile SET casual_interests = :old WHERE id = 1 AND casual_interests = :new"),
        {"new": _NEW_CASUAL_INTERESTS, "old": _OLD_CASUAL_INTERESTS},
    )
    conn.execute(
        sa.text("UPDATE now_items SET value = :old WHERE slug = 'listening' AND value = :new"),
        {"new": _NEW_LISTENING, "old": _OLD_LISTENING},
    )
    conn.execute(
        sa.text("UPDATE museum_exhibits SET body_md = :old WHERE slug = 'coming-of-age' AND body_md = :new"),
        {"new": _NEW_COMING_OF_AGE, "old": _OLD_COMING_OF_AGE},
    )
    conn.execute(
        sa.text("UPDATE museum_exhibits SET body_md = :old WHERE slug = 'the-court' AND body_md = :new"),
        {"new": _NEW_THE_COURT, "old": _OLD_THE_COURT},
    )
    conn.execute(
        sa.text("UPDATE museum_exhibits SET body_md = :old WHERE slug = 'the-workshop' AND body_md = :new"),
        {"new": _NEW_THE_WORKSHOP, "old": _OLD_THE_WORKSHOP},
    )
