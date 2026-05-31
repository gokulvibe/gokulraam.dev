"""Aggregator search endpoint backing the site-wide cmd+k modal.

Queries every editable content source and returns grouped, ranked results.
Plain substring + token-overlap scoring — fast enough at our scale; no
external search engine needed.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.auth import optional_admin
from app.db import get_db
from app.models import (
    BadmintonPlayer,
    BadmintonTournament,
    NowItem,
    Profile,
    Project,
    SpecialtyItem,
    TilPost,
    UsesItem,
    WorkAward,
    WorkCertification,
    WorkEducation,
    WorkRole,
)


router = APIRouter(prefix="/search", tags=["search"])


class SearchHit(BaseModel):
    group: str          # "TIL" | "Work" | "Projects" | …
    title: str
    subtitle: str = ""
    href: str
    score: int = 0


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]


def _score(query: str, *texts: str) -> int:
    """Crude relevance score. Higher = more relevant."""
    q = query.lower().strip()
    if not q:
        return 0
    blob = " ".join(t.lower() for t in texts if t)
    score = 0
    if q in blob:
        # bonus when full query appears as substring
        score += 20
        # extra bonus if the substring appears in the first text (usually title)
        if texts and q in texts[0].lower():
            score += 15
    # token overlap
    q_tokens = {t for t in q.split() if t}
    blob_tokens = set(blob.split())
    score += len(q_tokens & blob_tokens) * 5
    return score


def _emit(hits: list[SearchHit], hit: SearchHit, min_score: int = 1) -> None:
    if hit.score >= min_score:
        hits.append(hit)


@router.get("", response_model=SearchResponse)
def search(
    q: str,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[str | None, Depends(optional_admin)],
    limit: int = 30,
) -> SearchResponse:
    q = (q or "").strip()
    if len(q) < 1:
        return SearchResponse(query=q, hits=[])

    hits: list[SearchHit] = []

    # ── TIL posts ────────────────────────────────────────────
    til_stmt = select(TilPost)
    if not admin:
        til_stmt = til_stmt.where(TilPost.draft.is_(False))
    for p in db.scalars(til_stmt).all():
        s = _score(q, p.title, p.tags, p.body_md or "")
        _emit(hits, SearchHit(
            group="TIL",
            title=p.title,
            subtitle=p.tags or "",
            href=f"/til/{p.slug}",
            score=s + (5 if p.draft else 0),
        ))

    # ── Work roles ───────────────────────────────────────────
    for r in db.scalars(select(WorkRole)).all():
        s = _score(q, r.title, r.organization, r.bullets or "", r.stack or "")
        _emit(hits, SearchHit(
            group="Work",
            title=f"{r.title} · {r.organization}",
            subtitle=r.dates,
            href="/work",
            score=s,
        ))

    # ── Work awards ──────────────────────────────────────────
    for a in db.scalars(select(WorkAward)).all():
        s = _score(q, a.title, a.organization, a.description or "")
        _emit(hits, SearchHit(
            group="Awards",
            title=a.title,
            subtitle=f"{a.organization} · {a.year}".strip(" ·"),
            href="/work",
            score=s,
        ))

    # ── Certifications ───────────────────────────────────────
    for c in db.scalars(select(WorkCertification)).all():
        s = _score(q, c.name, c.issuer)
        _emit(hits, SearchHit(
            group="Certs",
            title=c.name,
            subtitle=c.issuer,
            href="/work",
            score=s,
        ))

    # ── Education ────────────────────────────────────────────
    for e in db.scalars(select(WorkEducation)).all():
        s = _score(q, e.school, e.degree, e.coursework or "", e.note or "")
        _emit(hits, SearchHit(
            group="Education",
            title=e.school,
            subtitle=e.degree,
            href="/work",
            score=s,
        ))

    # ── Projects ─────────────────────────────────────────────
    for pr in db.scalars(select(Project)).all():
        s = _score(q, pr.title, pr.summary or "", pr.stack or "", pr.award_tag or "")
        _emit(hits, SearchHit(
            group="Projects",
            title=pr.title,
            subtitle=pr.year,
            href="/projects",
            score=s,
        ))

    # ── Now items ────────────────────────────────────────────
    for item in db.scalars(select(NowItem)).all():
        s = _score(q, item.label or "", item.value)
        _emit(hits, SearchHit(
            group="Now",
            title=item.label or "(headline)",
            subtitle=item.value[:80],
            href="/now",
            score=s,
        ))

    # ── Uses items ───────────────────────────────────────────
    for u in db.scalars(select(UsesItem)).all():
        s = _score(q, u.name, u.note or "", u.category, "uses gear")
        _emit(hits, SearchHit(
            group="Uses",
            title=u.name,
            subtitle=f"{u.category} · {u.note}" if u.note else u.category,
            href="/uses",
            score=s,
        ))

    # ── Badminton players ────────────────────────────────────
    for pl in db.scalars(select(BadmintonPlayer)).all():
        s = _score(q, pl.name, "badminton player", pl.country, pl.discipline, pl.next_event or "")
        _emit(hits, SearchHit(
            group="Badminton",
            title=pl.name,
            subtitle=f"{pl.country} · {pl.discipline}",
            href="/badminton",
            score=s,
        ))

    # ── Badminton tournaments ────────────────────────────────
    for t in db.scalars(select(BadmintonTournament)).all():
        s = _score(q, t.name, "badminton tournament", t.location, t.tier, t.dates)
        _emit(hits, SearchHit(
            group="Badminton",
            title=t.name,
            subtitle=f"{t.location} · {t.tier}",
            href="/badminton",
            score=s,
        ))

    # ── Specialties (hero) ───────────────────────────────────
    for sp in db.scalars(select(SpecialtyItem)).all():
        s = _score(q, sp.name, sp.gloss or "")
        _emit(hits, SearchHit(
            group="Specialties",
            title=sp.name,
            subtitle=sp.gloss or "",
            href="/",
            score=s,
        ))

    # ── Profile fields (summary / about / location etc.) ─────
    profile = db.get(Profile, 1)
    if profile:
        for field, label in [
            ("summary", "Resume summary"),
            ("about_paragraph", "About (hero)"),
            ("intro_paragraph", "Hero intro"),
            ("skills_csv", "Skills"),
        ]:
            value = getattr(profile, field, "") or ""
            s = _score(q, label, value)
            _emit(hits, SearchHit(
                group="Profile",
                title=label,
                subtitle=value[:80],
                href="/resume" if field == "summary" else "/",
                score=s,
            ))

    hits.sort(key=lambda h: (-h.score, h.group, h.title))
    return SearchResponse(query=q, hits=hits[:limit])
