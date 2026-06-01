"""Photo log — camera roll of images.
Photos can be either external URLs (paste-and-go) or files uploaded
through /api/photos/upload (stored on the backend, served at /uploads/).

GET    public · POST/POST upload/PATCH/DELETE admin-only.
"""

import io
import secrets
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_admin
from app.db import get_db
from app.models import Photo
from app.schemas import PhotoCreate, PhotoOut, PhotoUpdate
from app.storage import get_storage


router = APIRouter(prefix="/photos", tags=["photos"])

MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB — generous-but-not-silly for photos.
ALLOWED_MIMES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp",
    "image/gif", "image/avif", "image/heic",
}


def _next_order(db: Session) -> int:
    max_order = db.scalar(select(Photo.order).order_by(Photo.order.desc()).limit(1)) or 0
    return max_order + 1


@router.get("", response_model=list[PhotoOut])
def list_photos(db: Annotated[Session, Depends(get_db)]) -> list[Photo]:
    return list(db.scalars(select(Photo).order_by(Photo.order, Photo.id)).all())


@router.post("", response_model=PhotoOut, status_code=status.HTTP_201_CREATED)
def create_photo(
    body: PhotoCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> Photo:
    photo = Photo(
        slug=f"p-{secrets.token_urlsafe(8)}",
        url=body.url.strip(),
        caption=body.caption.strip(),
        taken_at=body.taken_at.strip(),
        order=_next_order(db),
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


@router.post("/upload", response_model=PhotoOut, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
    caption: Annotated[str, Form()] = "",
    taken_at: Annotated[str, Form()] = "",
) -> Photo:
    """Multipart upload — `file` (the image) + optional `caption` + `taken_at`.
    Stores under photos/<uuid>.<ext>; the saved Photo row's `url` is the
    relative path `/uploads/photos/<uuid>.<ext>` and the frontend prefixes
    the API base."""
    mime = (file.content_type or "").lower()
    if mime not in ALLOWED_MIMES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"unsupported image type: {mime or 'unknown'}",
        )

    # Buffer the upload so we can enforce size before persisting.
    buf = io.BytesIO()
    size = 0
    while chunk := await file.read(64 * 1024):
        size += len(chunk)
        if size > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                f"file too large — max {MAX_UPLOAD_BYTES // 1024 // 1024} MB",
            )
        buf.write(chunk)
    buf.seek(0)

    ext = Path(file.filename or "img").suffix.lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".heic"}:
        ext = ".jpg"
    key = f"photos/{uuid.uuid4().hex}{ext}"

    get_storage().save(key, buf, mime)

    photo = Photo(
        slug=f"p-{secrets.token_urlsafe(8)}",
        url=f"/uploads/{key}",
        caption=(caption or "").strip(),
        taken_at=(taken_at or "").strip(),
        order=_next_order(db),
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

    # If this was a local upload, drop the file from disk too.
    if photo.url.startswith("/uploads/"):
        key = photo.url[len("/uploads/"):]
        try:
            get_storage().delete(key)
        except Exception:  # noqa: BLE001
            pass  # best-effort — DB row still gets removed

    db.delete(photo)
    db.commit()
