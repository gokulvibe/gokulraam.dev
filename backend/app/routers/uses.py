"""Uses-items router. Fixed category + slug; admin can edit name and note.
No POST or DELETE — keys are seeded."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_admin
from app.db import get_db
from app.models import UsesItem
from app.schemas import UsesItemOut, UsesItemUpdate


router = APIRouter(prefix="/uses", tags=["uses"])


@router.get("", response_model=list[UsesItemOut])
def list_items(db: Annotated[Session, Depends(get_db)]) -> list[UsesItem]:
    stmt = select(UsesItem).order_by(UsesItem.order, UsesItem.id)
    return list(db.scalars(stmt).all())


@router.patch("/{item_id}", response_model=UsesItemOut)
def update_item(
    item_id: int,
    body: UsesItemUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> UsesItem:
    item = db.get(UsesItem, item_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "uses item not found")
    if body.name is not None:
        item.name = body.name
    if body.note is not None:
        item.note = body.note
    db.commit()
    db.refresh(item)
    return item
