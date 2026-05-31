"""Profile router. Three resources under /api/profile:
  - the profile singleton (GET, PATCH /api/profile)
  - hero stats         (GET, PATCH /api/profile/stats/<id>)
  - specialty items    (GET, PATCH /api/profile/specialties/<id>)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_admin
from app.db import get_db
from app.models import Profile, ProfileStat, SpecialtyItem
from app.schemas import (
    ProfileOut,
    ProfileStatOut,
    ProfileStatUpdate,
    ProfileUpdate,
    SpecialtyItemOut,
    SpecialtyItemUpdate,
)


router = APIRouter(prefix="/profile", tags=["profile"])


def _patch(obj, body) -> None:
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)


# ─── Singleton profile ────────────────────────────────────────

@router.get("", response_model=ProfileOut)
def get_profile(db: Annotated[Session, Depends(get_db)]) -> Profile:
    profile = db.get(Profile, 1)
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "profile not seeded")
    return profile


@router.patch("", response_model=ProfileOut)
def update_profile(
    body: ProfileUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> Profile:
    profile = db.get(Profile, 1)
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "profile not seeded")
    _patch(profile, body)
    db.commit()
    db.refresh(profile)
    return profile


# ─── Hero stat tiles (4 of them) ──────────────────────────────

@router.get("/stats", response_model=list[ProfileStatOut])
def list_stats(db: Annotated[Session, Depends(get_db)]) -> list[ProfileStat]:
    return list(db.scalars(select(ProfileStat).order_by(ProfileStat.order)).all())


@router.patch("/stats/{stat_id}", response_model=ProfileStatOut)
def update_stat(
    stat_id: int,
    body: ProfileStatUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> ProfileStat:
    obj = db.get(ProfileStat, stat_id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "stat not found")
    _patch(obj, body)
    db.commit()
    db.refresh(obj)
    return obj


# ─── Specialty tiles (9 of them) ──────────────────────────────

@router.get("/specialties", response_model=list[SpecialtyItemOut])
def list_specialties(db: Annotated[Session, Depends(get_db)]) -> list[SpecialtyItem]:
    return list(db.scalars(select(SpecialtyItem).order_by(SpecialtyItem.order)).all())


@router.patch("/specialties/{item_id}", response_model=SpecialtyItemOut)
def update_specialty(
    item_id: int,
    body: SpecialtyItemUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> SpecialtyItem:
    obj = db.get(SpecialtyItem, item_id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "specialty not found")
    _patch(obj, body)
    db.commit()
    db.refresh(obj)
    return obj
