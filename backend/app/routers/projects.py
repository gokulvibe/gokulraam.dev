"""Projects router. List + PATCH. The `featured` flag is also editable so the
admin can promote any project into the /work "selected projects" section."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_admin
from app.db import get_db
from app.models import Project
from app.schemas import ProjectOut, ProjectUpdate


router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(
    db: Annotated[Session, Depends(get_db)],
    featured_only: bool = False,
) -> list[Project]:
    stmt = select(Project).order_by(Project.order, Project.id)
    if featured_only:
        stmt = stmt.where(Project.featured.is_(True))
    return list(db.scalars(stmt).all())


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> Project:
    obj = db.get(Project, project_id)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "project not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
