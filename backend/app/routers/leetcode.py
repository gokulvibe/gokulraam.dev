"""LeetCode public-profile cache endpoints.

GET   /api/leetcode           public — last-synced numbers
PATCH /api/leetcode           admin  — change configured username
POST  /api/leetcode/refresh   admin  — trigger an out-of-band scrape

The scrape itself lives in app.scrapers.leetcode and runs daily via
APScheduler (see main.py). These endpoints are just the read +
admin-controls surface.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import current_admin
from app.db import get_db
from app.models import LeetcodeStats
from app.schemas import LeetcodeStatsOut, LeetcodeStatsUpdate
from app.scrapers.leetcode import run_scrape


router = APIRouter(prefix="/leetcode", tags=["leetcode"])


def _row(db: Session) -> LeetcodeStats:
    """Return the singleton row, creating it lazily if missing. Keeps
    the rest of the endpoints from having to special-case 'maybe not
    seeded yet'."""
    row = db.get(LeetcodeStats, 1)
    if row is None:
        row = LeetcodeStats(id=1, username="")
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("", response_model=LeetcodeStatsOut)
def get_stats(db: Annotated[Session, Depends(get_db)]) -> LeetcodeStats:
    return _row(db)


@router.patch("", response_model=LeetcodeStatsOut)
def update_stats(
    body: LeetcodeStatsUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> LeetcodeStats:
    row = _row(db)
    if body.username is not None:
        new_username = body.username.strip()
        if new_username != row.username:
            row.username = new_username
            # Reset state when the username changes so we don't show
            # the old user's numbers under the new name.
            row.total_solved = 0
            row.easy_solved = 0
            row.medium_solved = 0
            row.hard_solved = 0
            row.streak_days = 0
            row.total_active_days = 0
            row.ranking = 0
            row.last_synced_at = None
            row.last_error = "" if new_username else "no username set"
    db.commit()
    db.refresh(row)
    return row


@router.post("/refresh", response_model=LeetcodeStatsOut)
async def refresh_stats(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> LeetcodeStats:
    row = _row(db)
    if not (row.username or "").strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "no username configured")
    await run_scrape()
    db.expire_all()
    return _row(db)
