"""Photo log — camera roll of external image URLs.
GET public · POST/PATCH/DELETE admin-only."""

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_admin
from app.db import get_db
from app.models import Photo
from app.schemas import PhotoCreate, PhotoOut, PhotoUpdate


router = APIRouter(prefix="/photos", tags=["photos"])


@router.get("", response_model=list[PhotoOut])
def list_photos(db: Annotated[Session, Depends(get_db)]) -> list[Photo]:
    return list(db.scalars(select(Photo).order_by(Photo.order, Photo.id)).all())


@router.post("", response_model=PhotoOut, status_code=status.HTTP_201_CREATED)
def create_photo(
    body: PhotoCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> Photo:
    # New photos go at the end (highest order). Slug is opaque — we don't
    # surface it in URLs, but the model requires a unique one.
    max_order = db.scalar(select(Photo.order).order_by(Photo.order.desc()).limit(1)) or 0
    slug = f"p-{secrets.token_urlsafe(8)}"
    photo = Photo(
        slug=slug,
        url=body.url.strip(),
        caption=body.caption.strip(),
        taken_at=body.taken_at.strip(),
        order=max_order + 1,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


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


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(
    photo_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> None:
    photo = db.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "photo not found")
    db.delete(photo)
    db.commit()
