"""Work router. Five resource collections (roles, awards, certifications, education),
admin-only PATCH on each. No POST/DELETE in v1 — slugs are seeded."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_admin
from app.db import get_db
from app.models import (
    WorkAward,
    WorkCertification,
    WorkEducation,
    WorkRole,
)
from app.schemas import (
    WorkAwardOut,
    WorkAwardUpdate,
    WorkCertificationOut,
    WorkCertificationUpdate,
    WorkEducationOut,
    WorkEducationUpdate,
    WorkRoleOut,
    WorkRoleUpdate,
)


router = APIRouter(prefix="/work", tags=["work"])


def _patch(obj, body) -> None:
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)


# ─── Roles ─────────────────────────────────────────────────────

@router.get("/roles", response_model=list[WorkRoleOut])
def list_roles(db: Annotated[Session, Depends(get_db)]) -> list[WorkRole]:
    return list(db.scalars(select(WorkRole).order_by(WorkRole.order, WorkRole.id)).all())


@router.patch("/roles/{role_id}", response_model=WorkRoleOut)
def update_role(
    role_id: int,
    body: WorkRoleUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> WorkRole:
    obj = db.get(WorkRole, role_id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "role not found")
    _patch(obj, body)
    db.commit()
    db.refresh(obj)
    return obj


# ─── Awards ────────────────────────────────────────────────────

@router.get("/awards", response_model=list[WorkAwardOut])
def list_awards(db: Annotated[Session, Depends(get_db)]) -> list[WorkAward]:
    return list(db.scalars(select(WorkAward).order_by(WorkAward.order, WorkAward.id)).all())


@router.patch("/awards/{award_id}", response_model=WorkAwardOut)
def update_award(
    award_id: int,
    body: WorkAwardUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> WorkAward:
    obj = db.get(WorkAward, award_id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "award not found")
    _patch(obj, body)
    db.commit()
    db.refresh(obj)
    return obj


# ─── Certifications ────────────────────────────────────────────

@router.get("/certifications", response_model=list[WorkCertificationOut])
def list_certifications(db: Annotated[Session, Depends(get_db)]) -> list[WorkCertification]:
    return list(
        db.scalars(select(WorkCertification).order_by(WorkCertification.order, WorkCertification.id)).all()
    )


@router.patch("/certifications/{cert_id}", response_model=WorkCertificationOut)
def update_certification(
    cert_id: int,
    body: WorkCertificationUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> WorkCertification:
    obj = db.get(WorkCertification, cert_id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "certification not found")
    _patch(obj, body)
    db.commit()
    db.refresh(obj)
    return obj


# ─── Education ─────────────────────────────────────────────────

@router.get("/education", response_model=list[WorkEducationOut])
def list_education(db: Annotated[Session, Depends(get_db)]) -> list[WorkEducation]:
    return list(
        db.scalars(select(WorkEducation).order_by(WorkEducation.order, WorkEducation.id)).all()
    )


@router.patch("/education/{edu_id}", response_model=WorkEducationOut)
def update_education(
    edu_id: int,
    body: WorkEducationUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> WorkEducation:
    obj = db.get(WorkEducation, edu_id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "education entry not found")
    _patch(obj, body)
    db.commit()
    db.refresh(obj)
    return obj
