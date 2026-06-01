"""Photo log — masonry grid of external image URLs.
GET public, PATCH admin-only."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_admin
from app.db import get_db
from app.models import Photo
from app.schemas import PhotoOut, PhotoUpdate


router = APIRouter(prefix="/photos", tags=["photos"])


@router.get("", response_model=list[PhotoOut])
def list_photos(db: Annotated[Session, Depends(get_db)]) -> list[Photo]:
    return list(db.scalars(select(Photo).order_by(Photo.order, Photo.id)).all())


@router.patch("/{photo_id}", response_model=PhotoOut)
def update_photo(
    photo_id: int,
    body: PhotoUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> Photo:
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "photo not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(photo, k, v)
    db.commit()
    db.refresh(photo)
    return photo
