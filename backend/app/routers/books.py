"""Bookshelf — books with status (reading / finished / want).
GET public, PATCH admin-only. Seeded with a small starting shelf."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_admin
from app.db import get_db
from app.models import Book
from app.schemas import BookOut, BookUpdate


router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=list[BookOut])
def list_books(db: Annotated[Session, Depends(get_db)]) -> list[Book]:
    return list(db.scalars(select(Book).order_by(Book.order, Book.id)).all())


@router.patch("/{book_id}", response_model=BookOut)
def update_book(
    book_id: int,
    body: BookUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> Book:
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "book not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(book, k, v)
    db.commit()
    db.refresh(book)
    return book
