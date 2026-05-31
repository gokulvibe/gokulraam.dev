from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import UPLOADS_DIR, get_settings
from app.db import Base, engine
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.migrate import run_migrations
from app.routers import auth, badminton, now, og, profile, projects, search, stats, status as status_router, til, uses, work
from app.scrapers.bwf import run_scrape
from app.seed import (
    seed_badminton,
    seed_now_items,
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
    Base.metadata.create_all(bind=engine)
    if (n := run_migrations()):
        print(f"[migrate] added {n} columns to existing tables")
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

app.include_router(auth.router, prefix="/api")
app.include_router(til.router, prefix="/api")
app.include_router(now.router, prefix="/api")
app.include_router(uses.router, prefix="/api")
app.include_router(badminton.router, prefix="/api")
app.include_router(work.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(og.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(status_router.router, prefix="/api")
app.include_router(stats.router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
