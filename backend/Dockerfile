# Backend image — built for portability, not currently used in prod.
#
# Render free tier today deploys from source (Python buildpack), not from
# Docker images. This Dockerfile exists so we can move to fly.io,
# Railway, DO App Platform, a paid Render plan, or self-hosting on a VPS
# with a single `docker build && docker push`.
#
# Build:
#   cd backend && docker build -t gokulraam-backend .
#
# Run (against any Postgres URL or default SQLite):
#   docker run --rm -p 8000:8000 \
#     -e DATABASE_URL='postgresql://...' \
#     -e ADMIN_USERNAME='gokul' \
#     -e ADMIN_PASSWORD_HASH='$2b$12$...' \
#     -e SESSION_SECRET='...' \
#     -e FRONTEND_ORIGIN='https://gokulraam-dev.pages.dev' \
#     -e COOKIE_SECURE='true' \
#     -e FRIEND_CODE='...' \
#     gokulraam-backend
#
# The container runs `python -m app.migrate && uvicorn` — same flow as
# Render's startCommand. Migrations apply BEFORE uvicorn binds the port.

# --- Stage: deps ---------------------------------------------------------
# Slim base + just the system libraries Pillow needs at runtime. Pip
# wheels cover psycopg2-binary, lxml, etc. — no need for build tooling.
FROM python:3.12-slim AS deps

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Pillow needs these at runtime for JPEG/zlib support. Everything else
# we depend on ships as a pre-built wheel.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        libjpeg62-turbo \
        zlib1g \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache the dependency layer separately from the source so iterating on
# code doesn't re-install Python deps every build.
COPY requirements.txt ./
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# --- Stage: runtime ------------------------------------------------------
FROM deps AS runtime

# Copy app code (alembic/, app/, scripts/, tools/, etc.).
COPY . .

# A non-root user is safer for any container running outside a
# trusted sandbox. Most hosting providers don't care, but it's free.
RUN useradd --create-home --shell /usr/sbin/nologin app \
 && chown -R app:app /app
USER app

# Render-style: port comes from $PORT env (defaults to 8000 for local).
ENV PORT=8000
EXPOSE 8000

# Entry: migrate, then serve. If migrate fails, container exits non-zero
# and the orchestrator (Kubernetes / fly / Render paid / docker-compose)
# treats the deploy as failed — same semantics we already have on Render.
CMD ["sh", "-c", "python -m app.migrate && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
