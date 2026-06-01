"""Lightweight page-view analytics.

POST /api/stats/track         (public)  — fire-and-forget page view ingest
GET  /api/stats/summary       (admin)   — counts: total · last 7d · last 30d · unique paths
GET  /api/stats/daily         (admin)   — daily view counts for the last N days
GET  /api/stats/top-paths     (admin)   — top paths by count
GET  /api/stats/top-referrers (admin)   — top referrers (host extracted)
GET  /api/stats/recent        (admin)   — last N raw page views

All admin endpoints exclude self-views (page_views.is_admin = True).
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import desc, distinct, func, select
from sqlalchemy.orm import Session

from app.auth import current_admin, optional_admin
from app.db import get_db
from app.models import PageView


router = APIRouter(prefix="/stats", tags=["stats"])


# ─── Schemas ─────────────────────────────────────────────────────


class TrackIn(BaseModel):
    path: str
    referrer: str = ""


class StatsSummary(BaseModel):
    total_views: int
    last_7_days: int
    last_30_days: int
    last_24_hours: int
    unique_paths: int
    first_view_at: datetime | None = None


class DailyView(BaseModel):
    date: str  # YYYY-MM-DD
    count: int


class TopPath(BaseModel):
    path: str
    count: int


class TopReferrer(BaseModel):
    host: str
    count: int


class PageViewRow(BaseModel):
    path: str
    referrer: str
    user_agent: str
    created_at: datetime


# ─── Track ───────────────────────────────────────────────────────


@router.post("/track", status_code=204)
def track(
    body: TrackIn,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[str | None, Depends(optional_admin)],
) -> None:
    db.add(
        PageView(
            path=body.path[:300],
            referrer=body.referrer[:500],
            user_agent=(request.headers.get("user-agent") or "")[:500],
            is_admin=admin is not None,
        )
    )
    db.commit()


# ─── Admin dashboards ────────────────────────────────────────────


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _public_views(db: Session):
    """Base query: only non-admin views."""
    return select(PageView).where(PageView.is_admin.is_(False))


@router.get("/summary", response_model=StatsSummary)
def summary(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> StatsSummary:
    now = _utcnow()
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    last_24h = now - timedelta(hours=24)

    total = db.scalar(
        select(func.count()).select_from(PageView).where(PageView.is_admin.is_(False))
    ) or 0
    in_7d = db.scalar(
        select(func.count())
        .select_from(PageView)
        .where(PageView.is_admin.is_(False), PageView.created_at >= last_7d)
    ) or 0
    in_30d = db.scalar(
        select(func.count())
        .select_from(PageView)
        .where(PageView.is_admin.is_(False), PageView.created_at >= last_30d)
    ) or 0
    in_24h = db.scalar(
        select(func.count())
        .select_from(PageView)
        .where(PageView.is_admin.is_(False), PageView.created_at >= last_24h)
    ) or 0
    unique_paths = db.scalar(
        select(func.count(distinct(PageView.path))).where(PageView.is_admin.is_(False))
    ) or 0
    first_at = db.scalar(
        select(func.min(PageView.created_at)).where(PageView.is_admin.is_(False))
    )

    return StatsSummary(
        total_views=total,
        last_7_days=in_7d,
        last_30_days=in_30d,
        last_24_hours=in_24h,
        unique_paths=unique_paths,
        first_view_at=first_at,
    )


@router.get("/daily", response_model=list[DailyView])
def daily(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
    days: int = 30,
) -> list[DailyView]:
    days = max(1, min(days, 365))
    now = _utcnow()
    since = now - timedelta(days=days)

    rows = db.execute(
        select(
            func.date(PageView.created_at).label("d"),
            func.count().label("n"),
        )
        .where(PageView.is_admin.is_(False), PageView.created_at >= since)
        .group_by(func.date(PageView.created_at))
        .order_by(func.date(PageView.created_at))
    ).all()

    # Convert DB rows to a dict for easy lookup
    by_date: dict[str, int] = {}
    for d, n in rows:
        # SQLite returns date as str, Postgres returns datetime.date
        key = d.isoformat() if hasattr(d, "isoformat") else str(d)
        by_date[key[:10]] = int(n)

    # Fill in zero-count days so the chart isn't ragged
    out: list[DailyView] = []
    cursor = since.date()
    end = now.date()
    while cursor <= end:
        out.append(DailyView(date=cursor.isoformat(), count=by_date.get(cursor.isoformat(), 0)))
        cursor += timedelta(days=1)
    return out


@router.get("/top-paths", response_model=list[TopPath])
def top_paths(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
    limit: int = 20,
) -> list[TopPath]:
    limit = max(1, min(limit, 100))
    rows = db.execute(
        select(PageView.path, func.count().label("n"))
        .where(PageView.is_admin.is_(False))
        .group_by(PageView.path)
        .order_by(desc("n"))
        .limit(limit)
    ).all()
    return [TopPath(path=p, count=int(n)) for p, n in rows]


@router.get("/top-referrers", response_model=list[TopReferrer])
def top_referrers(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
    limit: int = 15,
) -> list[TopReferrer]:
    limit = max(1, min(limit, 100))
    rows = db.execute(
        select(PageView.referrer)
        .where(PageView.is_admin.is_(False))
    ).all()

    # Aggregate by host (extracted from referrer URL). Direct visits go into a
    # synthetic "direct" bucket.
    counts: dict[str, int] = {}
    for (raw,) in rows:
        if not raw:
            counts["direct"] = counts.get("direct", 0) + 1
            continue
        try:
            host = urlparse(raw).netloc or "direct"
        except Exception:  # noqa: BLE001
            host = "direct"
        # Strip leading "www."
        if host.startswith("www."):
            host = host[4:]
        counts[host] = counts.get(host, 0) + 1

    items = sorted(counts.items(), key=lambda kv: -kv[1])[:limit]
    return [TopReferrer(host=h, count=n) for h, n in items]


@router.get("/recent", response_model=list[PageViewRow])
def recent(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
    limit: int = 50,
) -> list[PageViewRow]:
    limit = max(1, min(limit, 500))
    rows = db.scalars(
        select(PageView)
        .where(PageView.is_admin.is_(False))
        .order_by(desc(PageView.created_at))
        .limit(limit)
    ).all()
    return [
        PageViewRow(
            path=r.path,
            referrer=r.referrer,
            user_agent=r.user_agent,
            created_at=r.created_at,
        )
        for r in rows
    ]
