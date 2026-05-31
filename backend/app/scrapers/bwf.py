"""BWF / tournamentsoftware.com scraper.

Strategy
========

`tournamentsoftware.com` hosts every BWF tournament's draws under a stable URL
pattern. The scraper:

1. Pulls a curated set of tournament source URLs from the DB (each tournament
   has a `source_url` field admins can edit).
2. For tournaments with `source_url` populated, fetches the draw page and tries
   to identify match rows mentioning any tracked player (DB query — full names).
3. Writes those matches into the `badminton_matches` table, replacing any prior
   scraped match for the same player+tournament combo.
4. Falls back to the YAML at `backend/data/badminton-fallback.yaml` for
   tournaments themselves whenever the scrape produces nothing — so the
   /badminton page never goes blank.

Notes
=====

* This is intentionally pragmatic, not a perfect parser. tournamentsoftware HTML
  varies subtly per organiser; we use BeautifulSoup with a few heuristics and
  best-effort opponent / round / score extraction.
* If the HTML changes and the scraper can't find anything, we keep prior data;
  we only overwrite when the scrape clearly succeeded.
* Polling runs once a day via APScheduler (wired from main.py). Manual trigger:
    .venv/bin/python -c "from app.scrapers.bwf import run_scrape; run_scrape(verbose=True)"
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml
from bs4 import BeautifulSoup
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import BASE_DIR
from app.db import SessionLocal
from app.models import (
    BadmintonMatch,
    BadmintonPlayer,
    BadmintonTournament,
)


log = logging.getLogger("scraper.bwf")
FALLBACK_PATH = BASE_DIR / "data" / "badminton-fallback.yaml"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15 — gokulraam.dev scraper"
)


# ─── Fallback YAML loader ────────────────────────────────────────


def _load_fallback() -> dict:
    if not FALLBACK_PATH.exists():
        return {"tournaments": [], "matches": []}
    try:
        return yaml.safe_load(FALLBACK_PATH.read_text()) or {}
    except yaml.YAMLError as e:
        log.warning("could not parse fallback YAML: %s", e)
        return {"tournaments": [], "matches": []}


def _ensure_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _upsert_tournaments_from_fallback(db: Session) -> int:
    """If we have no tournaments at all (e.g. fresh DB), seed from YAML.
    Otherwise update only the structured start_date/end_date when missing."""
    data = _load_fallback()
    rows: list[dict] = data.get("tournaments", []) or []
    written = 0
    for r in rows:
        slug = r.get("slug")
        if not slug:
            continue
        existing = db.scalar(select(BadmintonTournament).where(BadmintonTournament.slug == slug))
        sd = r.get("start_date")
        ed = r.get("end_date")
        if isinstance(sd, str):
            sd = datetime.fromisoformat(sd).replace(tzinfo=timezone.utc)
        if isinstance(ed, str):
            ed = datetime.fromisoformat(ed).replace(tzinfo=timezone.utc)
        if existing is None:
            existing = BadmintonTournament(
                slug=slug,
                name=r.get("name", slug),
                location=r.get("location", ""),
                tier=r.get("tier", ""),
                dates=r.get("dates", ""),
                start_date=sd,
                end_date=ed,
                order=999,
            )
            db.add(existing)
            written += 1
        else:
            changed = False
            if existing.start_date is None and sd:
                existing.start_date = sd
                changed = True
            if existing.end_date is None and ed:
                existing.end_date = ed
                changed = True
            if not existing.dates and r.get("dates"):
                existing.dates = r["dates"]
                changed = True
            if changed:
                written += 1
    if written:
        db.commit()
    return written


# ─── Live draw scraping ──────────────────────────────────────────


def _fetch_html(url: str) -> str | None:
    try:
        with httpx.Client(
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=httpx.Timeout(15.0),
        ) as client:
            r = client.get(url)
            if r.status_code >= 400:
                log.warning("scrape failed %s → HTTP %s", url, r.status_code)
                return None
            return r.text
    except httpx.RequestError as e:
        log.warning("scrape error %s → %s", url, e)
        return None


def _scrape_tournament_matches(html: str, players: list[BadmintonPlayer]) -> list[dict]:
    """Best-effort extraction of matches mentioning any tracked player.
    Returns a list of dicts shaped for BadmintonMatch."""
    soup = BeautifulSoup(html, "html.parser")
    matches: list[dict] = []
    name_to_player = {p.name.lower(): p for p in players}
    # Also index by short names (last name of doubles partner, first name)
    short_to_player = {}
    for p in players:
        for token in p.name.replace("/", " ").split():
            if len(token) > 3:
                short_to_player.setdefault(token.lower(), p)

    # Heuristic: tournamentsoftware uses <tr> rows in tables for match lists.
    # Within each row, the player names appear as <a> or plain text. We scan rows.
    rows = soup.find_all("tr")
    seen: set[tuple[int, str]] = set()  # (player_id, opponent_text)
    for row in rows:
        text = row.get_text(" ", strip=True).lower()
        for full_name, player in name_to_player.items():
            if full_name in text:
                # Try to extract opponent: take the row's text and remove the player
                cleaned = row.get_text(" | ", strip=True)
                parts = [p.strip() for p in cleaned.split(" | ") if p.strip()]
                opponent = ""
                for p_text in parts:
                    if player.name.lower() not in p_text.lower() and len(p_text) > 3:
                        opponent = p_text[:200]
                        break
                key = (player.id, opponent)
                if key in seen:
                    continue
                seen.add(key)
                matches.append(
                    {
                        "player_id": player.id,
                        "opponent": opponent or "TBD",
                        "round": "",  # too HTML-variant to extract reliably here
                        "scheduled_at": None,
                        "status": "scheduled",
                        "score": "",
                    }
                )
                break
    return matches


def _scrape_one_tournament(
    db: Session,
    tour: BadmintonTournament,
    players: list[BadmintonPlayer],
) -> int:
    """Returns number of match rows written for this tournament."""
    if not tour.source_url:
        return 0
    html = _fetch_html(tour.source_url)
    if html is None:
        return 0
    matches = _scrape_tournament_matches(html, players)
    if not matches:
        return 0
    # Replace previous matches for this tournament
    db.execute(delete(BadmintonMatch).where(BadmintonMatch.tournament_id == tour.id))
    for m in matches:
        db.add(BadmintonMatch(tournament_id=tour.id, **m))
    db.commit()
    return len(matches)


# ─── Public entry point ──────────────────────────────────────────


def run_scrape(verbose: bool = False) -> dict:
    """Top-level scrape. Returns a small summary dict for logging."""
    summary = {
        "tournaments_seeded": 0,
        "tournaments_scraped": 0,
        "matches_written": 0,
        "errors": [],
    }
    with SessionLocal() as db:
        # Step 1: backfill tournament list / structured dates from fallback YAML.
        summary["tournaments_seeded"] = _upsert_tournaments_from_fallback(db)

        # Step 2: scrape each tournament that has a source_url.
        players = list(db.scalars(select(BadmintonPlayer)).all())
        tours = list(
            db.scalars(
                select(BadmintonTournament).where(BadmintonTournament.source_url != "")
            ).all()
        )
        for tour in tours:
            try:
                n = _scrape_one_tournament(db, tour, players)
                summary["tournaments_scraped"] += 1
                summary["matches_written"] += n
            except Exception as e:  # noqa: BLE001
                summary["errors"].append(f"{tour.slug}: {e!r}")

    if verbose:
        log.info("scrape summary: %s", summary)
    return summary
