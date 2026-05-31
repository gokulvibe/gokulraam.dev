"""Now-items router. Fixed slugs (headline + 6 facets); admin can only edit
the `value` field. No POST or DELETE — keys are seeded and stable."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_admin
from app.db import get_db
from app.models import NowItem
from app.schemas import NowItemOut, NowItemUpdate


router = APIRouter(prefix="/now", tags=["now"])


@router.get("", response_model=list[NowItemOut])
def list_items(db: Annotated[Session, Depends(get_db)]) -> list[NowItem]:
    return list(db.scalars(select(NowItem).order_by(NowItem.order)).all())


@router.patch("/{slug}", response_model=NowItemOut)
def update_item(
    slug: str,
    body: NowItemUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> NowItem:
    item = db.scalar(select(NowItem).where(NowItem.slug == slug))
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "now item not found")
    item.value = body.value
    db.commit()
    db.refresh(item)
    return item
