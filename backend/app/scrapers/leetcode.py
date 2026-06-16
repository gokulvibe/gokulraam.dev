"""LeetCode public-profile scraper.

LeetCode has no official public API, but their site uses a GraphQL
endpoint at https://leetcode.com/graphql that returns public profile
data without authentication. Used by leetcard, leetcode-stats-api,
and dozens of similar tools.

We POST a single query, parse the response, and upsert the singleton
LeetcodeStats row (id=1) on every scrape. Cached server-side by the
daily APScheduler cron — visitors hitting /api/leetcode just read the
row, no live network call.

If LeetCode changes their schema or rate-limits us, the scrape
records the error on the row's `last_error` field and the existing
numbers stay visible (graceful degradation).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select

from app.db import SessionLocal
from app.models import LeetcodeStats


log = logging.getLogger(__name__)


_GRAPHQL = "https://leetcode.com/graphql"

# Combined query covering everything we display. The matchedUser block
# returns null when the username doesn't exist — we treat that as an
# error (so the admin can fix the typo) rather than zeroing out values.
_QUERY = """
query userPublicProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile { ranking }
    submitStats {
      acSubmissionNum { difficulty count }
    }
    userCalendar { streak totalActiveDays }
  }
}
"""

# Browser-like UA so we don't get a Cloudflare challenge.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com/",
}


async def _fetch(username: str) -> dict:
    payload = {"query": _QUERY, "variables": {"username": username}}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(_GRAPHQL, json=payload, headers=_HEADERS)
        r.raise_for_status()
        return r.json()


def _parse(data: dict) -> dict | None:
    """Map a GraphQL response into LeetcodeStats field values. Returns
    None if the user wasn't found (data.matchedUser is null)."""
    user = (data.get("data") or {}).get("matchedUser")
    if not user:
        return None

    submit = user.get("submitStats", {}).get("acSubmissionNum", []) or []
    by_diff = {row["difficulty"]: row["count"] for row in submit}

    cal = user.get("userCalendar") or {}
    profile = user.get("profile") or {}

    return {
        "total_solved": int(by_diff.get("All", 0)),
        "easy_solved": int(by_diff.get("Easy", 0)),
        "medium_solved": int(by_diff.get("Medium", 0)),
        "hard_solved": int(by_diff.get("Hard", 0)),
        "streak_days": int(cal.get("streak", 0) or 0),
        "total_active_days": int(cal.get("totalActiveDays", 0) or 0),
        "ranking": int(profile.get("ranking", 0) or 0),
    }


async def run_scrape() -> None:
    """Update the singleton LeetcodeStats row from leetcode.com.

    Reads the configured username from the row; if empty, no-op. On
    transport / parse failure, the row's `last_error` is set and
    numerical fields are left untouched (stale data is better than
    zeroed data)."""
    with SessionLocal() as db:
        row = db.get(LeetcodeStats, 1)
        if row is None or not (row.username or "").strip():
            log.info("leetcode: no username configured — skipping")
            return

        username = row.username.strip()
        try:
            raw = await _fetch(username)
        except httpx.HTTPError as e:
            row.last_error = f"network: {e}"[:300]
            row.updated_at = datetime.now(tz=timezone.utc)
            db.commit()
            log.warning("leetcode: fetch failed for %s: %s", username, e)
            return

        # Some GraphQL responses return 200 with an `errors` block.
        if raw.get("errors"):
            row.last_error = f"graphql: {raw['errors'][:1]!r}"[:300]
            row.updated_at = datetime.now(tz=timezone.utc)
            db.commit()
            log.warning("leetcode: graphql errors for %s: %s", username, raw["errors"])
            return

        parsed = _parse(raw)
        if parsed is None:
            row.last_error = f"user '{username}' not found on leetcode"
            row.updated_at = datetime.now(tz=timezone.utc)
            db.commit()
            log.warning("leetcode: no such user %s", username)
            return

        for k, v in parsed.items():
            setattr(row, k, v)
        row.last_error = ""
        row.last_synced_at = datetime.now(tz=timezone.utc)
        db.commit()
        log.info("leetcode: synced %s — %d solved, %d-day streak",
                 username, row.total_solved, row.streak_days)
