"""Public guestbook.

POST /api/guestbook       — anonymous submission. Honeypot field + IP hash for
                            light spam protection. No login required.
GET  /api/guestbook       — list visible entries.
DELETE /api/guestbook/<id> (admin) — hide an entry (soft-delete via hidden=True).
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth import current_admin
from app.db import get_db
from app.models import GuestbookEntry
from app.schemas import GuestbookEntryIn, GuestbookEntryOut


router = APIRouter(prefix="/guestbook", tags=["guestbook"])


def _ip_hash(request: Request) -> str:
    # IP arrives through various headers depending on the proxy chain
    # (Render → us). Take the leftmost public-facing IP.
    raw = (
        request.headers.get("cf-connecting-ip")
        or request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "")
    )
    if not raw:
        return ""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


@router.get("", response_model=list[GuestbookEntryOut])
def list_entries(db: Annotated[Session, Depends(get_db)]) -> list[GuestbookEntry]:
    return list(
        db.scalars(
            select(GuestbookEntry)
            .where(GuestbookEntry.hidden.is_(False))
            .order_by(desc(GuestbookEntry.created_at))
            .limit(200)
        ).all()
    )


@router.post("", response_model=GuestbookEntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(
    body: GuestbookEntryIn,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> GuestbookEntry:
    # Honeypot: bots tend to fill every visible-looking input. Our 'website'
    # field is hidden via CSS — if it's populated, it's a bot. We respond
    # with a fake success so the bot doesn't retry, but never insert.
    if body.website.strip():
        # Synthesise a successful-looking response without persisting.
        return GuestbookEntry(  # type: ignore[return-value]
            id=0,
            name=body.name or "anonymous",
            message=body.message,
            ip_hash="",
            hidden=True,
            created_at=datetime.now(tz=timezone.utc),
        )

    ip = _ip_hash(request)
    # Light rate limit: same IP can't post twice within 30 seconds.
    if ip:
        recent = db.scalar(
            select(GuestbookEntry)
            .where(
                GuestbookEntry.ip_hash == ip,
                GuestbookEntry.created_at >= datetime.now(tz=timezone.utc) - timedelta(seconds=30),
            )
            .limit(1)
        )
        if recent:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "easy there — wait a moment before posting again",
            )

    entry = GuestbookEntry(
        name=(body.name or "").strip()[:80],
        message=body.message.strip(),
        ip_hash=ip,
        hidden=False,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def hide_entry(
    entry_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> None:
    entry = db.get(GuestbookEntry, entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "entry not found")
    entry.hidden = True
    db.commit()
