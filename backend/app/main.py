from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import UPLOADS_DIR, get_settings
from app.db import Base, engine
from app.routers import auth, badminton, now, profile, projects, stats, til, uses, work
from app.seed import (
    seed_badminton,
    seed_now_items,
    seed_profile,
    seed_projects,
    seed_til_from_mdx,
    seed_uses_items,
    seed_work,
)


@asynccontextmanager
async def lifespan(_: FastAPI):  # noqa: ANN201
    Base.metadata.create_all(bind=engine)
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
    yield


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
app.include_router(stats.router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
