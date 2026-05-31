"""Live 'currently' status.

POST /api/status     (admin) — write a new ping
GET  /api/status     (public) — read the current state with computed aliveness

Aliveness rules (purely server-side from last_seen_at age):
  age <  3 min → "live"
  age < 15 min → "idle"
  otherwise    → "away"
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status as http
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_admin
from app.db import get_db
from app.models import StatusPing
from app.schemas import StatusOut, StatusPingIn


router = APIRouter(prefix="/status", tags=["status"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aliveness(age_seconds: int) -> str:
    if age_seconds < 3 * 60:
        return "live"
    if age_seconds < 15 * 60:
        return "idle"
    return "away"


def _to_out(p: StatusPing) -> StatusOut:
    last = p.last_seen_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    started = p.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    age = int((_utcnow() - last).total_seconds())
    return StatusOut(
        state=p.state,
        detail=p.detail,
        started_at=started,
        last_seen_at=last,
        age_seconds=age,
        aliveness=_aliveness(age),
    )


@router.get("", response_model=StatusOut)
def get_status(db: Annotated[Session, Depends(get_db)]) -> StatusOut:
    p = db.scalar(select(StatusPing).order_by(StatusPing.id.desc()))
    if not p:
        # Never been pinged — return a synthetic "away" state.
        now = _utcnow()
        return StatusOut(
            state="away",
            detail="",
            started_at=now,
            last_seen_at=now - (now - now),  # zero delta, but renders sanely
            age_seconds=999999,
            aliveness="away",
        )
    return _to_out(p)


@router.post("", response_model=StatusOut, status_code=http.HTTP_201_CREATED)
def post_status(
    body: StatusPingIn,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> StatusOut:
    now = _utcnow()
    p = db.scalar(select(StatusPing).order_by(StatusPing.id.desc()))
    if p and p.state == body.state:
        # Same state — extend last_seen_at, keep started_at so duration grows.
        p.detail = body.detail
        p.last_seen_at = now
    else:
        # State changed (or first ping) — new row.
        p = StatusPing(
            state=body.state,
            detail=body.detail,
            started_at=now,
            last_seen_at=now,
        )
        db.add(p)
    db.commit()
    db.refresh(p)
    return _to_out(p)
