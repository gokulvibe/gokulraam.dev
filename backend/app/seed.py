"""Seed TIL posts from MDX files on first boot when the table is empty.

Reads `../frontend/src/content/til/*.mdx`, parses frontmatter, inserts rows.
Idempotent — skips slugs that already exist. Safe to call every startup.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from slugify import slugify
from sqlalchemy import select

from app.config import BASE_DIR
from app.db import SessionLocal
from app.models import (
    BadmintonPlayer,
    BadmintonTournament,
    Book,
    LeetcodeStats,
    LogbookEntry,
    MuseumExhibit,
    NowItem,
    Photo,
    Profile,
    ProfileStat,
    Project,
    SpecialtyItem,
    TilPost,
    UsesItem,
    WorkAward,
    WorkCertification,
    WorkEducation,
    WorkRole,
)


# Path to MDX content. Relative to repo root.
MDX_DIR = BASE_DIR.parent / "frontend" / "src" / "content" / "til"

_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Tiny YAML-ish frontmatter parser. Just keys and string/list values."""
    match = _FRONTMATTER.match(text)
    if not match:
        return {}, text
    raw, body = match.groups()
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        v = v.strip()
        # strip wrapping quotes
        if (v.startswith('"') and v.endswith('"')) or (
            v.startswith("'") and v.endswith("'")
        ):
            v = v[1:-1]
        meta[k.strip()] = v
    return meta, body.strip()


def _parse_tags(raw: str) -> list[str]:
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1]
        return [t.strip().strip("'\"") for t in inner.split(",") if t.strip()]
    return [t.strip() for t in raw.split(",") if t.strip()]


def _parse_date(raw: str) -> datetime:
    # Accept "YYYY-MM-DD" or ISO datetime
    raw = raw.strip()
    try:
        if len(raw) == 10:
            return datetime.strptime(raw, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(raw)
    except ValueError:
        return datetime.now(tz=timezone.utc)


_NOW_DEFAULTS: list[tuple[str, str, str, int]] = [
    # (slug, label, value, order). Headline has empty label — it's the
    # quick-text on the homepage card face. The other eight are the facets
    # shown on /now (flat 2-col grid).
    ("headline",  "",          "Tuning a CSV → Postgres pipeline. 12× faster, and counting.", 0),
    ("building",  "building",  "this folio. astro · fastapi · sqlite.", 1),
    ("at-work",   "at work",   "csv → postgres ingestion. threading + lru_cache. 12× faster.", 2),
    ("reading",   "reading",   "Designing Data-Intensive Applications — Kleppmann.", 3),
    ("watching",  "watching",  "BWF Tour. Lakshya, Shi Yu Qi, Lee Zii Jia, Satwik–Chirag.", 4),
    ("listening", "listening", "lo-fi loops + ambient. whatever ships code.", 5),
    ("learning",  "learning",  "distributed systems fundamentals. async FastAPI patterns.", 6),
    ("playing",   "playing",   "badminton. working on the backhand. it remains unreliable.", 7),
    ("following", "following", "@hnasr · @b0rk · swyx · BWF livestream feeds.", 8),
]


def seed_now_items() -> int:
    """Idempotent. Inserts any missing default rows. Existing rows are
    left untouched so admin edits survive across restarts."""
    changed = 0
    with SessionLocal() as db:
        existing = {row.slug for row in db.scalars(select(NowItem)).all()}
        for slug, label, value, order in _NOW_DEFAULTS:
            if slug not in existing:
                db.add(NowItem(slug=slug, label=label, value=value, order=order))
                changed += 1
        if changed:
            db.commit()
    return changed


# (category, slug, name, note). Order is implied by list position; we'll
# stamp `order` accordingly when inserting.
_USES_DEFAULTS: list[tuple[str, str, str, str]] = [
    # code
    ("code", "vscode",          "VS Code",            "editor · vim bindings"),
    ("code", "one-dark-pro",    "One Dark Pro",       "theme"),
    ("code", "jetbrains-mono",  "JetBrains Mono",     "editor font"),
    ("code", "iterm2",          "iTerm2",             "terminal"),
    ("code", "zsh",             "zsh + oh-my-zsh",    "shell"),
    ("code", "starship",        "Starship",           "prompt"),
    # runtime
    ("runtime", "python",       "Python 3.12",        "primary language"),
    ("runtime", "postgres",     "PostgreSQL 16",      "database of choice"),
    ("runtime", "redis",        "Redis 7",            "cache · queues"),
    ("runtime", "fastapi",      "FastAPI",            "modern python apis"),
    ("runtime", "pytest",       "Pytest",             "unit + integration"),
    ("runtime", "pydantic",     "Pydantic v2",        "data validation"),
    # hardware
    ("hardware", "laptop",      "MacBook",            "daily driver · macOS"),
    ("hardware", "keyboard",    "— keyboard",         "fill in your real one"),
    ("hardware", "monitor",     "— monitor",          "fill in"),
    ("hardware", "mouse",       "— mouse",            "fill in"),
    # sound
    ("sound", "headphones",     "— headphones",       "fill in"),
    ("sound", "speakers",       "— speakers",         "fill in"),
    ("sound", "playlist",       "— playlist",         "lo-fi · ambient · whatever ships code"),
    # court
    ("court", "racquet",        "— racquet",          "fill in (e.g. Yonex Astrox 99)"),
    ("court", "shoes",          "— shoes",            "fill in (e.g. Yonex Power Cushion)"),
    ("court", "shuttles",       "— shuttles",         "fill in (e.g. Yonex Mavis 350)"),
    ("court", "bag",            "— bag",              "fill in"),
    # fitness
    ("fitness", "shaker",       "Protein shaker",     "shake. drink. recover."),
    ("fitness", "whey",         "Whey protein",       "post-session staple"),
    ("fitness", "dumbbells",    "Dumbbells",          "home strength · upper-body day"),
    ("fitness", "bands",        "— resistance bands", "fill in if you use any"),
    ("fitness", "mat",          "— mat",              "fill in"),
    # daily
    ("daily", "watch",          "— watch",            "fill in"),
    ("daily", "wallet",         "— wallet",           "fill in"),
    ("daily", "notebook",       "— notebook",         "fill in (e.g. Moleskine)"),
    ("daily", "coffee",         "Coffee",             "before code · before court"),
]


def seed_uses_items() -> int:
    with SessionLocal() as db:
        existing = db.scalar(select(UsesItem.id).limit(1))
        if existing is not None:
            return 0
        for order, (category, slug, name, note) in enumerate(_USES_DEFAULTS):
            db.add(UsesItem(category=category, slug=slug, name=name, note=note, order=order))
        db.commit()
        return len(_USES_DEFAULTS)


_BADMINTON_PLAYERS: list[tuple[str, str, str, str, str, str]] = [
    # (slug, name, country, flag, discipline, next_event)
    ("lakshya-sen",    "Lakshya Sen",                              "IND", "🇮🇳", "Men's Singles", "Indonesia Open · 02 Jun"),
    ("lee-zii-jia",    "Lee Zii Jia",                              "MAS", "🇲🇾", "Men's Singles", "Indonesia Open · 02 Jun"),
    ("satwik-chirag",  "Satwiksairaj Rankireddy / Chirag Shetty",  "IND", "🇮🇳", "Men's Doubles", "Indonesia Open · 02 Jun"),
    ("shi-yu-qi",      "Shi Yu Qi",                                "CHN", "🇨🇳", "Men's Singles", "Indonesia Open · 02 Jun"),
]

_BADMINTON_TOURNAMENTS: list[tuple[str, str, str, str, str]] = [
    # (slug, name, dates, location, tier)
    ("indonesia-open-2026",      "Indonesia Open",          "02–07 Jun 2026",       "Jakarta",         "Super 1000"),
    ("malaysia-masters-2026",    "Malaysia Masters",        "09–14 Jun 2026",       "Kuala Lumpur",    "Super 500"),
    ("us-open-2026",             "US Open",                 "23–28 Jun 2026",       "Council Bluffs",  "Super 300"),
    ("canada-open-2026",         "Canada Open",             "30 Jun – 05 Jul 2026", "Calgary",         "Super 300"),
]


def seed_badminton() -> int:
    inserted = 0
    with SessionLocal() as db:
        if db.scalar(select(BadmintonPlayer.id).limit(1)) is None:
            for order, (slug, name, country, flag, discipline, next_event) in enumerate(_BADMINTON_PLAYERS):
                db.add(BadmintonPlayer(
                    slug=slug, name=name, country=country, flag=flag,
                    discipline=discipline, next_event=next_event, order=order,
                ))
                inserted += 1
        if db.scalar(select(BadmintonTournament.id).limit(1)) is None:
            for order, (slug, name, dates, location, tier) in enumerate(_BADMINTON_TOURNAMENTS):
                db.add(BadmintonTournament(
                    slug=slug, name=name, dates=dates, location=location,
                    tier=tier, order=order,
                ))
                inserted += 1
        if inserted:
            db.commit()
    return inserted


# ─── Work seeds ───────────────────────────────────────────────────

_SAAMA_SE_BULLETS = """\
Owned end-to-end design and development of core modules, maintaining 99.9% uptime and stability for hundreds of users.
Engineered a global Redis caching utility for high-frequency app configurations — 6× faster server operations, reduced DB load.
Optimized complex SQL queries — 60× reduction in execution latency for frequently accessed APIs.
Architected normalized PostgreSQL databases used by multiple services, eliminating data redundancy and ensuring 100% consistency.
Refactored legacy components using SOLID principles, enabling reliability and new feature extension with zero regression issues.
Identified and remediated critical security vulnerabilities — SQL Injection, IDOR, weak cryptography — securing the production env.
Lead peer code reviews and PR evaluations to enforce code quality and standards."""

_SAAMA_INTERN_BULLETS = """\
Designed and developed flexible RESTful APIs with Flask used by different client applications.
Used Pydantic to define and validate JSONs, importing structured data into PostgreSQL from unstructured CSV files.
Boosted data pre-processing and validation performance by 12× using threading and lru_cache.
Regularly wrote unit and integration tests using Pytest.
Developed global utilities, reducing redundant code and bugs, improving development efficiency for the entire engineering team."""

_FREELANCE_JOB_PORTAL_BULLETS = """\
Led a team of 7 building a job portal application end-to-end.
Designed the database normalised to 3NF, consistent, no duplication.
Planned and built REST APIs in Django, wired up an HTML/CSS/JS frontend."""

_FREELANCE_CLAYTON_BULLETS = """\
Built a React web app for an Australian Chettinad restaurant.
Shipped as a PWA — installable, offline-capable.
Reusable components, code base structured for easy extension."""


def seed_work() -> int:
    inserted = 0
    with SessionLocal() as db:
        # Roles
        if db.scalar(select(WorkRole.id).limit(1)) is None:
            roles = [
                # Saama
                ("saama-se", "saama", "Software Engineer", "Saama Technologies",
                 "Coimbatore", "Dec 2023 → present",
                 _SAAMA_SE_BULLETS,
                 "Python,PostgreSQL,Redis,Celery,SOLID,Security", "", 0),
                ("saama-intern", "saama", "Software Engineering Intern", "Saama Technologies",
                 "Coimbatore", "Apr 2022 → Dec 2023",
                 _SAAMA_INTERN_BULLETS,
                 "Python,Flask,Pydantic,PostgreSQL,Pytest", "", 1),
                # Freelance
                ("freelance-job-portal", "freelance", "Project Coordinator · Backend Developer",
                 "Job Portal", "", "2021 → 2022",
                 _FREELANCE_JOB_PORTAL_BULLETS,
                 "Django,REST,PostgreSQL,Team Lead", "", 2),
                ("freelance-clayton", "freelance", "Frontend Developer",
                 "Clayton Chettinad — Restaurant Website", "", "2021 → 2022",
                 _FREELANCE_CLAYTON_BULLETS,
                 "React,PWA,Service Workers",
                 "https://clayton-chettinad.netlify.app/", 3),
            ]
            for r in roles:
                db.add(WorkRole(
                    slug=r[0], section=r[1], title=r[2], organization=r[3],
                    location=r[4], dates=r[5], bullets=r[6], stack=r[7],
                    link=r[8], order=r[9],
                ))
                inserted += 1

        # Awards
        if db.scalar(select(WorkAward.id).limit(1)) is None:
            awards = [
                ("hackathon-2025", "Best Technical Implementation & Execution", "2025",
                 "Saama Hackathon",
                 "AI-driven Protocol Document standardizer. Robust background job pipeline using FastAPI to digitize PDFs to interpretable JSONs.",
                 0),
                ("hackathon-2024", "Special Recognition Award", "2024", "Saama Hackathon",
                 "Interactive web debugger for the SDQ product. Built for the engineering team to inspect runtime state without local setup.",
                 1),
                ("mg-scholarship", "MG Scholarship", "", "Kumaraguru College of Technology",
                 "Awarded during B.E. CSE for sustained academic standing.", 2),
            ]
            for a in awards:
                db.add(WorkAward(slug=a[0], title=a[1], year=a[2], organization=a[3],
                                 description=a[4], order=a[5]))
                inserted += 1

        # Certifications
        if db.scalar(select(WorkCertification.id).limit(1)) is None:
            for order, name in enumerate(["Python", "REST APIs", "SQL", "Java", "JavaScript"]):
                db.add(WorkCertification(
                    slug=f"hackerrank-{name.lower().replace(' ', '-')}",
                    name=name, issuer="HackerRank", order=order,
                ))
                inserted += 1

        # Education
        if db.scalar(select(WorkEducation.id).limit(1)) is None:
            db.add(WorkEducation(
                slug="kct-be-cse",
                school="Kumaraguru College of Technology",
                degree="B.E. Computer Science & Engineering",
                gpa="9.3/10",
                dates="2019 → 2023",
                coursework="DBMS,DSA,OOP,SDLC",
                note="MG Scholarship for academic performance.",
                order=0,
            ))
            inserted += 1

        if inserted:
            db.commit()
    return inserted


def seed_projects() -> int:
    inserted = 0
    with SessionLocal() as db:
        if db.scalar(select(Project.id).limit(1)) is not None:
            return 0
        projects = [
            ("protocol-standardizer", "AI Protocol Document Standardizer", "2025",
             "Hackathon-winning tool that digitizes clinical protocol PDFs into structured, interpretable JSON. Background job pipeline using FastAPI for async processing.",
             "FastAPI,Python,PDF parsing,LLM,Background jobs",
             "", "★ hackathon 2025", True, 0),
            ("naviguide", "NaviGuide — Activity Recommendation System", "2022–2023",
             "Highly scalable activity recommendation system for the college campus. New users get recommendations based on chats of previous users. Activities stream to Kafka, processed in real time on distributed PySpark nodes.",
             "PySpark,Kafka,Flask,Distributed systems",
             "https://github.com/Sanjay8322/NaviGuide", "", True, 1),
            ("sdq-debugger", "SDQ Interactive Web Debugger", "2024",
             "Web-based interactive debugger built for the SDQ product. Allowed engineers to inspect runtime state and reproduce issues without local setup.",
             "Python,Web,Debugging tools",
             "", "★ hackathon 2024", False, 2),
            ("clayton-chettinad-pwa", "Clayton Chettinad — Restaurant PWA", "2021–2022",
             "React PWA for an Australian Chettinad restaurant. Installable and works offline. Reusable component architecture for easy extension.",
             "React,PWA,Service Workers",
             "https://clayton-chettinad.netlify.app/", "", False, 3),
        ]
        for p in projects:
            db.add(Project(
                slug=p[0], title=p[1], year=p[2], summary=p[3], stack=p[4],
                link=p[5], award_tag=p[6], featured=p[7], order=p[8],
            ))
            inserted += 1
        db.commit()
    return inserted


# ─── Profile seeds ────────────────────────────────────────────────

_PROFILE = {
    "first_name": "Gokul",
    "last_name": "Raam",
    "role_title": "Backend Engineer",
    "organization": "Saama Technologies",
    "location_short": "Coimbatore",
    "location_full": "Coimbatore, Tamil Nadu · IND",
    "email": "dev.gokulraam@gmail.com",
    "phone": "+91 9361404560",
    "github_url": "https://github.com/gokulvibe",
    "linkedin_url": "https://linkedin.com/in/gokulraam",
    "cv_url": "/resume.pdf",
    "intro_paragraph": (
        "I write APIs that are really fast and really easy to maintain. "
        "Day job at Saama — three years in, six× cache speedups, sixty× query optimizations. "
        "Night job — chasing a more reliable defensive backhand."
    ),
    "about_paragraph": (
        "Backend engineer at Saama since 2022. Three years building fast, secure REST "
        "APIs in Python. Specialised in finding the slow line, deleting it, and "
        "keeping the rest readable. Currently into distributed systems, Postgres "
        "internals, and a badly-needed backhand."
    ),
    "summary": (
        "Backend engineer specialised in writing RESTful APIs that are really fast and easy "
        "to maintain. Experienced in crafting reusable modules, optimising queries, finding "
        "and fixing security hotspots. Have worked with Python, Redis, PostgreSQL, Celery."
    ),
    "skills_csv": "Python,FastAPI,Flask,Django,PostgreSQL,Redis,Celery,Pydantic,Pytest,SQLAlchemy,PySpark,Kafka",
    # Plain-English bio for the "Daylight" light theme (non-dev visitors)
    "casual_about": (
        "I work as a software engineer at Saama in Coimbatore, where we build "
        "tools for clinical research. Outside work, you'll usually find me on a "
        "badminton court, in the gym, or with a book."
    ),
    "casual_interests": "Badminton, Fitness, Reading, Music",
}

_PROFILE_STATS: list[tuple[str, str, str, str]] = [
    # (slug, label, primary, secondary)
    ("title",  "Title",     "Software Engineer", "@ Saama Tech"),
    ("locale", "Locale",    "Coimbatore",        "Tamil Nadu · IND"),
    ("class",  "Class",     "Backend",           "Python · PG · Redis"),
    ("status", "Available", "Listening",         "for the right room"),
]

_SPECIALTIES: list[tuple[str, str, str, str]] = [
    # (slug, name, gloss, metric)
    ("caching",         "Caching",           "redis · hot configs",          "6×"),
    ("query-tuning",    "Query Tuning",      "postgres · indexing · plans",  "60×"),
    ("async-threading", "Async / Threading", "threading · lru_cache",        "12×"),
    ("api-design",      "API Design",        "restful · modular · pydantic", ""),
    ("schema-design",   "Schema Design",     "normalised postgres · 3nf",    ""),
    ("security",        "Security",          "sqli · idor · crypto",         ""),
    ("background-jobs", "Background Jobs",   "celery · fastapi pipelines",   ""),
    ("solid-refactors", "SOLID Refactors",   "zero-regression rewrites",     ""),
    ("code-reviews",    "Code Reviews",      "standards · mentorship",       ""),
]


def seed_profile() -> int:
    inserted = 0
    with SessionLocal() as db:
        existing = db.get(Profile, 1)
        if existing is None:
            db.add(Profile(id=1, **_PROFILE))
            inserted += 1
        else:
            # Backfill any newly-added field that's still empty on the existing
            # row (so migrating to new schema fields doesn't require manual edit)
            for key in ("casual_about", "casual_interests"):
                if hasattr(existing, key) and not (getattr(existing, key) or "").strip():
                    setattr(existing, key, _PROFILE.get(key, ""))
                    inserted += 1
        if db.scalar(select(ProfileStat.id).limit(1)) is None:
            for order, (slug, label, primary, secondary) in enumerate(_PROFILE_STATS):
                db.add(ProfileStat(slug=slug, label=label, primary=primary,
                                   secondary=secondary, order=order))
                inserted += 1
        if db.scalar(select(SpecialtyItem.id).limit(1)) is None:
            for order, (slug, name, gloss, metric) in enumerate(_SPECIALTIES):
                db.add(SpecialtyItem(slug=slug, name=name, gloss=gloss,
                                     metric=metric, order=order))
                inserted += 1
        if inserted:
            db.commit()
    return inserted


# ─── Museum exhibits (friends-only /museum) ──────────────────────

_MUSEUM_DEFAULTS: list[tuple[str, str, str, str, str, str, str]] = [
    # (slug, room_label, title, kicker, body_md, photo_url, photo_caption)
    (
        "entrance",
        "ROOM I · ENTRANCE",
        "Welcome, traveller.",
        "this is where I keep the things I show only to people I trust.",
        (
            "If you're here, it's because someone gave you the code. Thank you for coming.\n\n"
            "The other parts of this site are for recruiters and strangers. They're shiny and full of "
            "metrics and tech stacks. This place is quieter — closer to a small museum a friend invited "
            "you into. Take your time. Wander."
        ),
        "",
        "",
    ),
    (
        "origins",
        "ROOM II · ORIGINS",
        "Coimbatore, late nineties.",
        "where I came from.",
        (
            "Replace this with the story of where you grew up — the streets, the smells, the family "
            "you came from. A paragraph or two. Friends like reading this kind of thing more than "
            "you'd guess.\n\n"
            "(You can drop a childhood photo above — just paste an Imgur or GitHub user-content URL "
            "into the photo field.)"
        ),
        "",
        "",
    ),
    (
        "coming-of-age",
        "ROOM III · COMING OF AGE",
        "Kumaraguru, four years.",
        "college, friends, the first time I wrote anything that worked.",
        (
            "Replace this with what college was like — late nights, the first big project, the "
            "friends you kept, the ones you lost. The moment code clicked. NaviGuide was here.\n\n"
            "Photos from that time go a long way."
        ),
        "",
        "",
    ),
    (
        "the-court",
        "ROOM IV · THE COURT",
        "Badminton, every week without fail.",
        "the thing I look forward to most.",
        (
            "Replace this with your court story — when you started, the players you watch, the time "
            "you actually beat someone better than you, the time you didn't. The backhand you've been "
            "chasing for two years.\n\n"
            "Action shot would land beautifully here."
        ),
        "",
        "",
    ),
    (
        "the-workshop",
        "ROOM V · THE WORKSHOP",
        "What's making me tick right now.",
        "current chapter.",
        (
            "Replace this with whatever's currently lighting you up — a project, a book, a person, "
            "a question you can't put down. The 'now', but more honest than the public /now page.\n\n"
            "This room can change as often as you like."
        ),
        "",
        "",
    ),
    (
        "closing",
        "ROOM VI · CLOSING NOTE",
        "Thanks for visiting.",
        "before you go.",
        (
            "Replace this with anything you want friends to take away — a thank-you, a poem you like, "
            "an open invitation. Maybe a way to reach you that isn't email.\n\n"
            "I'm glad you came."
        ),
        "",
        "",
    ),
]


_BOOK_DEFAULTS: list[tuple[str, str, str, str, str, str]] = [
    # (slug, title, author, status, year, note)
    ("ddia", "Designing Data-Intensive Applications", "Martin Kleppmann",
     "reading", "2017",
     "The book every backend engineer recommends. Living up to the hype."),
    ("the-go-programming-language", "The Go Programming Language", "Donovan & Kernighan",
     "want", "2015",
     "Replace this with anything you want to read next."),
    ("the-pragmatic-programmer", "The Pragmatic Programmer", "Hunt & Thomas",
     "finished", "1999",
     "Read it twice — first time too early, second time it clicked."),
    ("zero-to-one", "Zero to One", "Peter Thiel",
     "finished", "2014",
     "Counterintuitive in places, prescient in others."),
    ("placeholder-1", "— add a book", "— author",
     "reading", "",
     "Sign in as admin and click any field to edit. Cover URLs can be any public image link."),
]


# Sample photos sourced from picsum.photos (stable, license-free). Replace
# with real photos by admin-editing the url field on each card. Mix of
# landscape + portrait aspect ratios so the camera-roll layout reads as
# real photography, not a uniform grid.
_PHOTO_DEFAULTS: list[tuple[str, str, str, str]] = [
    # (slug, url, caption, taken_at)
    ("yelagiri-dawn",    "https://picsum.photos/id/1018/1600/1000",
     "Yelagiri at dawn",              "Mar 2026"),
    ("cauvery-evening",  "https://picsum.photos/id/1015/900/1200",
     "Cauvery, late afternoon",       "Jan 2026"),
    ("western-ghats",    "https://picsum.photos/id/1019/1400/900",
     "Western Ghats green",           "Feb 2026"),
    ("first-coffee",     "https://picsum.photos/id/431/900/1200",
     "First coffee · before the court", "Apr 2026"),
    ("last-game",        "https://picsum.photos/id/1062/1600/1000",
     "Last game of the night",        "May 2026"),
    ("apartment-walk",   "https://picsum.photos/id/180/1200/800",
     "Walk around the apartment",     "May 2026"),
    ("ooty-monsoon",     "https://picsum.photos/id/164/1400/900",
     "Ooty · monsoon",                "Aug 2025"),
    ("desk-1am",         "https://picsum.photos/id/119/1200/800",
     "Desk · 1am, almost shipped it", "Apr 2026"),
]


def seed_photos() -> int:
    """Seed sample photos. Reseeds if the only rows present are empty
    placeholders (so old empty rows are replaced once)."""
    with SessionLocal() as db:
        rows = list(db.scalars(select(Photo)).all())
        if rows and any((r.url or "").strip() for r in rows):
            return 0  # admin has real content — leave it alone
        for r in rows:
            db.delete(r)  # wipe empty placeholders
        for order, (slug, url, caption, taken_at) in enumerate(_PHOTO_DEFAULTS):
            db.add(Photo(slug=slug, url=url, caption=caption, taken_at=taken_at, order=order))
        db.commit()
        return len(_PHOTO_DEFAULTS)


def seed_books() -> int:
    with SessionLocal() as db:
        if db.scalar(select(Book.id).limit(1)) is not None:
            return 0
        for order, (slug, title, author, status, year, note) in enumerate(_BOOK_DEFAULTS):
            db.add(Book(
                slug=slug, title=title, author=author, status=status,
                year=year, note=note, order=order,
            ))
        db.commit()
        return len(_BOOK_DEFAULTS)


# ─── Logbook seed (short-form observations) ──────────────────

_LOGBOOK_DEFAULTS: list[tuple[str, str, int]] = [
    # (body, tag, hours_ago)
    ("First entry of the logbook. TIL was getting lonely.", "noted", 1),
    ("Watched Lakshya pull a backhand cross-court drop on match point. The kind of shot I'm two years away from.", "watching", 18),
    ("Found out about Postgres generated columns. How did I never use these?", "win", 44),
    ("Pre-coffee. Already wishing I had two.", "thought", 72),
]


_LEETCODE_DEFAULT_USERNAME = "gokulraamofficial"


def seed_leetcode() -> int:
    """Create the singleton LeetcodeStats row if it doesn't exist.
    Username defaults to Gokul's handle; admin can change later via
    PATCH /api/leetcode or the inline editor on /now. The daily cron
    then populates the numbers."""
    with SessionLocal() as db:
        if db.get(LeetcodeStats, 1) is not None:
            return 0
        db.add(LeetcodeStats(id=1, username=_LEETCODE_DEFAULT_USERNAME))
        db.commit()
        return 1


def seed_logbook() -> int:
    """Seed only when the table is empty."""
    from datetime import timedelta
    with SessionLocal() as db:
        if db.scalar(select(LogbookEntry.id).limit(1)) is not None:
            return 0
        now = datetime.now(tz=timezone.utc)
        for body, tag, hours_ago in _LOGBOOK_DEFAULTS:
            db.add(LogbookEntry(
                body=body,
                tag=tag,
                created_at=now - timedelta(hours=hours_ago),
            ))
        db.commit()
        return len(_LOGBOOK_DEFAULTS)


def seed_museum() -> int:
    with SessionLocal() as db:
        if db.scalar(select(MuseumExhibit.id).limit(1)) is not None:
            return 0
        for order, (slug, room_label, title, kicker, body_md, photo_url, photo_caption) in enumerate(_MUSEUM_DEFAULTS):
            db.add(MuseumExhibit(
                slug=slug,
                room_label=room_label,
                title=title,
                kicker=kicker,
                body_md=body_md,
                photo_url=photo_url,
                photo_caption=photo_caption,
                order=order,
            ))
        db.commit()
        return len(_MUSEUM_DEFAULTS)


def seed_til_from_mdx() -> int:
    """Returns the number of newly inserted posts."""
    if not MDX_DIR.exists():
        return 0

    inserted = 0
    with SessionLocal() as db:
        # Only seed when table is empty — keeps this safe to call always.
        existing_count = db.scalar(select(TilPost.id).limit(1))
        if existing_count is not None:
            return 0

        for path in sorted(MDX_DIR.glob("*.mdx")) + sorted(MDX_DIR.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            meta, body = _parse_frontmatter(text)
            if not meta.get("title"):
                continue
            slug = slugify(path.stem)
            if db.scalar(select(TilPost).where(TilPost.slug == slug)):
                continue
            post = TilPost(
                slug=slug,
                title=meta["title"],
                body_md=body,
                tags=",".join(_parse_tags(meta.get("tags", ""))),
                draft=str(meta.get("draft", "false")).lower() in ("true", "1", "yes"),
                created_at=_parse_date(meta.get("date", "")),
            )
            db.add(post)
            inserted += 1

        if inserted:
            db.commit()

    return inserted
