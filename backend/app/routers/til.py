import shutil
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import current_admin, optional_admin
from app.config import UPLOADS_DIR
from app.db import get_db
from app.markdown import render_markdown
from app.models import TilAttachment, TilPost
from app.schemas import TilAttachmentOut, TilPostCreate, TilPostOut, TilPostUpdate


router = APIRouter(prefix="/til", tags=["til"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def _unique_slug(db: Session, base: str) -> str:
    candidate = slugify(base) or "post"
    if not db.scalar(select(TilPost).where(TilPost.slug == candidate)):
        return candidate
    i = 2
    while db.scalar(select(TilPost).where(TilPost.slug == f"{candidate}-{i}")):
        i += 1
    return f"{candidate}-{i}"


def _to_out(post: TilPost) -> TilPostOut:
    return TilPostOut(
        id=post.id,
        slug=post.slug,
        title=post.title,
        body_md=post.body_md,
        body_html=render_markdown(post.body_md),
        tags=[t for t in post.tags.split(",") if t],
        draft=post.draft,
        created_at=post.created_at,
        updated_at=post.updated_at,
        attachments=[TilAttachmentOut.model_validate(a) for a in post.attachments],
    )


@router.get("", response_model=list[TilPostOut])
def list_posts(
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[str | None, Depends(optional_admin)],
    include_drafts: bool = False,
) -> list[TilPostOut]:
    # Only authenticated admins can request drafts.
    if include_drafts and not admin:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "admin required for drafts")
    stmt = select(TilPost).options(selectinload(TilPost.attachments)).order_by(TilPost.created_at.desc())
    if not include_drafts:
        stmt = stmt.where(TilPost.draft.is_(False))
    return [_to_out(p) for p in db.scalars(stmt).all()]


@router.get("/{slug}", response_model=TilPostOut)
def get_post(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[str | None, Depends(optional_admin)],
) -> TilPostOut:
    post = db.scalar(
        select(TilPost).options(selectinload(TilPost.attachments)).where(TilPost.slug == slug)
    )
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "post not found")
    # Drafts are only visible to the admin.
    if post.draft and not admin:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "post not found")
    return _to_out(post)


@router.post("", response_model=TilPostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    body: TilPostCreate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> TilPostOut:
    post = TilPost(
        slug=_unique_slug(db, body.title),
        title=body.title,
        body_md=body.body_md,
        tags=",".join(body.tags),
        draft=body.draft,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _to_out(post)


@router.patch("/{post_id}", response_model=TilPostOut)
def update_post(
    post_id: int,
    body: TilPostUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> TilPostOut:
    post = db.get(TilPost, post_id)
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "post not found")
    if body.title is not None:
        post.title = body.title
    if body.body_md is not None:
        post.body_md = body.body_md
    if body.tags is not None:
        post.tags = ",".join(body.tags)
    if body.draft is not None:
        post.draft = body.draft
    db.commit()
    db.refresh(post)
    return _to_out(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> None:
    post = db.get(TilPost, post_id)
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "post not found")
    for att in post.attachments:
        Path(UPLOADS_DIR / att.stored_path).unlink(missing_ok=True)
    db.delete(post)
    db.commit()


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> None:
    att = db.get(TilAttachment, attachment_id)
    if not att:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "attachment not found")
    Path(UPLOADS_DIR / att.stored_path).unlink(missing_ok=True)
    db.delete(att)
    db.commit()


@router.post("/{post_id}/attachments", response_model=TilAttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    post_id: int,
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> TilAttachmentOut:
    post = db.get(TilPost, post_id)
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "post not found")

    safe_name = Path(file.filename or "file").name
    stored_name = f"{post_id}-{uuid.uuid4().hex[:8]}-{safe_name}"
    dest = UPLOADS_DIR / stored_name

    size = 0
    with dest.open("wb") as out:
        while chunk := await file.read(64 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "file too large")
            out.write(chunk)

    att = TilAttachment(
        post_id=post_id,
        filename=safe_name,
        stored_path=stored_name,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=size,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return TilAttachmentOut.model_validate(att)
