from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse

from app.config import UPLOADS_DIR, get_settings
from app.storage import R2Storage, get_storage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Schema migrations live in alembic/ and run via `python -m app.migrate`
# (called from Makefile / Render's startCommand BEFORE uvicorn binds).
# Nothing migration-related runs in the lifespan anymore — keeps server
# boot focused on application bring-up, not DDL.
from app.routers import auth, badminton, books, guestbook, logbook, museum, now, og, photos, profile, projects, search, stats, status as status_router, til, uses, work
from app.scrapers.bwf import run_scrape
from app.seed import (
    seed_badminton,
    seed_books,
    seed_logbook,
    seed_museum,
    seed_now_items,
    seed_photos,
    seed_profile,
    seed_projects,
    seed_til_from_mdx,
    seed_uses_items,
    seed_work,
)


_scheduler: AsyncIOScheduler | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):  # noqa: ANN201
    global _scheduler
    # Schema is managed by Alembic — run `python -m app.migrate` (or
    # `make migrate`) before starting uvicorn. We deliberately don't
    # touch the schema from here. Seeds, scheduler, and other
    # application bring-up follow.
    if (n := seed_til_from_mdx()):
        print(f"[seed] imported {n} TIL posts from MDX")
    if (n := seed_now_items()):
        print(f"[seed] inserted {n} now items")
    if (n := seed_uses_items()):
        print(f"[seed] inserted {n} uses items")
    if (n := seed_badminton()):
        print(f"[seed] inserted {n} badminton rows")
    if (n := seed_work()):
        print(f"[seed] inserted {n} work rows")
    if (n := seed_projects()):
        print(f"[seed] inserted {n} projects")
    if (n := seed_profile()):
        print(f"[seed] inserted {n} profile rows")
    if (n := seed_museum()):
        print(f"[seed] inserted {n} museum exhibits")
    if (n := seed_books()):
        print(f"[seed] inserted {n} books")
    if (n := seed_photos()):
        print(f"[seed] inserted {n} photo placeholders")
    if (n := seed_logbook()):
        print(f"[seed] inserted {n} logbook entries")

    # Schedule daily badminton scrape at 06:00 local time. Best-effort —
    # failures don't crash startup; errors land in logs.
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        run_scrape,
        CronTrigger(hour=6, minute=0),
        id="badminton_scrape",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    _scheduler.start()
    print("[cron] scheduled daily badminton scrape at 06:00")

    yield

    if _scheduler:
        _scheduler.shutdown(wait=False)


settings = get_settings()

app = FastAPI(title="gokulraam.dev API", lifespan=lifespan)

# Allow multiple frontend origins for prod + previews + local dev.
# Comma-separated in env: "https://gokulraam.dev,https://*.pages.dev,http://localhost:4321"
_allowed_origins = [o.strip() for o in settings.frontend_origin.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom upload server: local-disk file response, OR 302-redirect to R2 public URL.
# Single endpoint so the frontend URL shape stays stable across hosts.
@app.get("/uploads/{path:path}")
def serve_upload(path: str):
    storage = get_storage()
    if isinstance(storage, R2Storage):
        url = storage.public_url(path)
        if not url:
            raise HTTPException(status_code=500, detail="R2 public URL not configured")
        return RedirectResponse(url, status_code=302)
    # Local disk
    target = Path(UPLOADS_DIR / path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    # Make sure we're not serving outside UPLOADS_DIR (defence-in-depth)
    try:
        target.resolve().relative_to(UPLOADS_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=404, detail="file not found") from None
    return FileResponse(target)

app.include_router(auth.router, prefix="/api")
app.include_router(til.router, prefix="/api")
app.include_router(now.router, prefix="/api")
app.include_router(uses.router, prefix="/api")
app.include_router(badminton.router, prefix="/api")
app.include_router(work.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(og.router, prefix="/api")
app.include_router(museum.router, prefix="/api")
app.include_router(books.router, prefix="/api")
app.include_router(photos.router, prefix="/api")
app.include_router(guestbook.router, prefix="/api")
app.include_router(logbook.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(status_router.router, prefix="/api")
app.include_router(stats.router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
