from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import PageView


router = APIRouter(prefix="/stats", tags=["stats"])


class TrackIn(BaseModel):
    path: str
    referrer: str = ""


@router.post("/track", status_code=204)
def track(body: TrackIn, request: Request, db: Annotated[Session, Depends(get_db)]) -> None:
    db.add(
        PageView(
            path=body.path[:300],
            referrer=body.referrer[:500],
            user_agent=(request.headers.get("user-agent") or "")[:500],
        )
    )
    db.commit()


@router.get("/summary")
def summary(db: Annotated[Session, Depends(get_db)]) -> list[dict[str, int | str]]:
    rows = db.execute(
        select(PageView.path, func.count().label("n"))
        .group_by(PageView.path)
        .order_by(func.count().desc())
        .limit(50)
    ).all()
    return [{"path": p, "views": n} for p, n in rows]
