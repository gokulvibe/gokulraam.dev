"""Museum router. Friends-only personal exhibits.

GET  /api/museum            → list of exhibits (requires friend or admin cookie)
PATCH /api/museum/<id>      → update one exhibit (admin only)

No POST/DELETE in v1 — the set of rooms is seeded and curated.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_admin, museum_visitor
from app.db import get_db
from app.markdown import render_markdown
from app.models import MuseumExhibit
from app.schemas import MuseumExhibitOut, MuseumExhibitUpdate


router = APIRouter(prefix="/museum", tags=["museum"])


def _to_out(exhibit: MuseumExhibit) -> dict:
    return {
        "id": exhibit.id,
        "slug": exhibit.slug,
        "room_label": exhibit.room_label,
        "title": exhibit.title,
        "kicker": exhibit.kicker,
        "body_md": exhibit.body_md,
        # `body_html` rendered fresh for clients that don't have a md renderer
        "body_html": render_markdown(exhibit.body_md or ""),
        "photo_url": exhibit.photo_url,
        "photo_caption": exhibit.photo_caption,
        "order": exhibit.order,
        "updated_at": exhibit.updated_at,
    }


@router.get("")
def list_exhibits(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(museum_visitor)],
) -> list[dict]:
    rows = db.scalars(
        select(MuseumExhibit).order_by(MuseumExhibit.order, MuseumExhibit.id)
    ).all()
    return [_to_out(r) for r in rows]


@router.patch("/{exhibit_id}", response_model=MuseumExhibitOut)
def update_exhibit(
    exhibit_id: int,
    body: MuseumExhibitUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> MuseumExhibit:
    exhibit = db.get(MuseumExhibit, exhibit_id)
    if not exhibit:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "exhibit not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(exhibit, k, v)
    db.commit()
    db.refresh(exhibit)
    return exhibit
