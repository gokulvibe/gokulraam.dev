"""Logbook — short-form observations.

GET    /api/logbook            — public, lists visible entries (newest first)
POST   /api/logbook            — admin, creates entry
PATCH  /api/logbook/<id>       — admin, edits body/tag
DELETE /api/logbook/<id>       — admin, soft-hides
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth import current_admin
from app.db import get_db
from app.models import LogbookEntry
from app.schemas import LogbookEntryCreate, LogbookEntryOut, LogbookEntryUpdate


router = APIRouter(prefix="/logbook", tags=["logbook"])


@router.get("", response_model=list[LogbookEntryOut])
def list_entries(db: Annotated[Session, Depends(get_db)]) -> list[LogbookEntry]:
    return list(
        db.scalars(
            select(LogbookEntry)
            .where(LogbookEntry.hidden.is_(False))
            .order_by(desc(LogbookEntry.created_at))
            .limit(300)
        ).all()
    )


@router.post("", response_model=LogbookEntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(
    body: LogbookEntryCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> LogbookEntry:
    entry = LogbookEntry(body=body.body.strip(), tag=body.tag.strip())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.patch("/{entry_id}", response_model=LogbookEntryOut)
def update_entry(
    entry_id: int,
    patch: LogbookEntryUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> LogbookEntry:
    entry = db.get(LogbookEntry, entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "entry not found")
    if patch.body is not None:
        entry.body = patch.body.strip()
    if patch.tag is not None:
        entry.tag = patch.tag.strip()
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def hide_entry(
    entry_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> None:
    entry = db.get(LogbookEntry, entry_id)
    if not entry:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "entry not found")
    entry.hidden = True
    db.commit()
