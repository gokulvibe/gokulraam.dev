"""Badminton router. DB-backed players + tournaments.
Admin can PATCH any field; no add/delete in v1.

Phase 3 will add structured DateTime fields on tournaments and a scraper
that populates the table from tournamentsoftware.com.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_admin
from app.db import get_db
from app.models import BadmintonPlayer, BadmintonTournament
from app.schemas import (
    BadmintonPlayerOut,
    BadmintonPlayerUpdate,
    BadmintonTournamentOut,
    BadmintonTournamentUpdate,
)


router = APIRouter(prefix="/badminton", tags=["badminton"])


# ─── Players ─────────────────────────────────────────────────────

@router.get("/players", response_model=list[BadmintonPlayerOut])
def list_players(db: Annotated[Session, Depends(get_db)]) -> list[BadmintonPlayer]:
    stmt = select(BadmintonPlayer).order_by(BadmintonPlayer.order, BadmintonPlayer.id)
    return list(db.scalars(stmt).all())


@router.patch("/players/{player_id}", response_model=BadmintonPlayerOut)
def update_player(
    player_id: int,
    body: BadmintonPlayerUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> BadmintonPlayer:
    p = db.get(BadmintonPlayer, player_id)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "player not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


# ─── Tournaments ─────────────────────────────────────────────────

@router.get("/tournaments", response_model=list[BadmintonTournamentOut])
def list_tournaments(db: Annotated[Session, Depends(get_db)]) -> list[BadmintonTournament]:
    stmt = select(BadmintonTournament).order_by(BadmintonTournament.order, BadmintonTournament.id)
    return list(db.scalars(stmt).all())


@router.patch("/tournaments/{tournament_id}", response_model=BadmintonTournamentOut)
def update_tournament(
    tournament_id: int,
    body: BadmintonTournamentUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(current_admin)],
) -> BadmintonTournament:
    t = db.get(BadmintonTournament, tournament_id)
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "tournament not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


# ─── Legacy compat ──────────────────────────────────────────────
# Kept so anything that still calls /api/badminton/upcoming gets a sensible
# response. Returns the current tournament list.

@router.get("/upcoming", response_model=list[BadmintonTournamentOut])
def upcoming(db: Annotated[Session, Depends(get_db)]) -> list[BadmintonTournament]:
    return list_tournaments(db)
