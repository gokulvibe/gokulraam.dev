# Claude Code — project context

> Auto-loaded by Claude Code at the start of every session. Keep it tight.
> Anything that drifts more than once a week belongs here.

## What this is

Gokul Raam's personal site + dev portfolio. Editorial dark TCG-folio aesthetic
("Nocturnal Folio") plus a light "Daylight" theme for non-dev visitors.
Every page is admin-editable in place — Jira-style inline edits, no separate
admin pages besides `/admin/login` and `/admin/stats`.

## Stack

| Layer | Local | Production |
|---|---|---|
| Frontend | Astro 4 (hybrid) + Tailwind + MDX + React islands @ `localhost:4321` | Cloudflare Pages — `gokulraam-dev.pages.dev` |
| Backend | FastAPI + uvicorn @ `localhost:8000` | Render free — `gokulraam-backend.onrender.com` |
| DB | SQLite (`backend/app.db`) | Neon Postgres (free tier, pooled) |
| Storage | Local disk (`backend/data/uploads/`) | LocalDisk on Render (ephemeral) — R2 ready when card available |

## Run

```sh
make install    # one-time
make dev        # both servers
```

Frontend hot-reloads on file change. Backend uses `--reload` so it picks up Python changes.

## Identity (this repo only)

- Git: `gokulvibe` / `gokulraamofficial@gmail.com` (NOT the global Saama identity)
- Admin login: username `gokul`, password is bcrypt-hashed in `backend/.env` (`ADMIN_PASSWORD_HASH`)

## Repo layout

```
frontend/src/
  pages/         Astro routes (one file per URL)
    admin/       login.astro + stats.astro
    museum/      enter.astro + index.astro
    til/         index.astro + [...slug].astro + rss.xml.ts
    404.astro    custom 404
  components/
    admin/       Editable* + AdminBar + LogbookCompose/Delete + PhotoAdd/Delete + StatsDashboard
    *.tsx        public-facing islands (CmdK, EasterEggs, LiveStatus, ThemeToggle, etc.)
  layouts/Base.astro    HEAD, nav, footer, all global islands
  lib/api.ts            single fetch client, credentials: 'include'
  styles/globals.css    ~2700 lines — design tokens + page-specific blocks
backend/app/
  main.py          FastAPI app + lifespan (migrate → seed → cron)
  models.py        all SQLAlchemy models
  schemas.py       all Pydantic schemas
  migrate.py       idempotent ALTER TABLE ADD COLUMN list
  seed.py          per-model seed functions (idempotent)
  storage.py       LocalDiskStorage | R2Storage, selected by env
  auth.py          admin cookie + friend (museum) cookie
  routers/         one router per domain
  scrapers/bwf.py  badminton scraper
DEPLOY.md          step-by-step prod walkthrough
ROADMAP.md         status + changelog (auth on what's shipped)
SPEC.md            product spec + design system + content-editing convention
```

## Conventions

### Inline-edit convention (SPEC §5)

Every editable field is a React island:
1. `useIsAdmin()` → if not admin, render the public view
2. Click → swap to input + `[save] [cancel]`
3. Save → typed PATCH (`/api/<thing>/<id>`)
4. Pages with editables must `export const prerender = false` (SSR per request)
5. Save broadcasts `CustomEvent('editable:saved', { detail })` so peer islands sync

Generic component: `EditableField` with `format: text | longtext | bullets | chips`
and `adminOnly?: boolean`. Specialized variants for one-off shapes: `EditableTitle`,
`EditableTags`, `EditableBody`, `EditableNowItem`, `EditableUsesField`.

**Important**: hooks BEFORE early returns. `useIsAdmin` and all `useState` must
run before `if (...) return null`. The `adminOnly` prop sits below all hooks.

### Card expander

Homepage cards open via `ExpandableCard.astro` (`data-expandable` on `<article>`).
The expander in `Base.astro` `cloneNode(true)`s the card and shows it as a modal.

**Editing is disabled in the expanded clone** via CSS (`.card-clone .editable--admin {
pointer-events: none }`). The clone's React island is a fresh hydration that
can't sync back, so we route admins to the dedicated section page instead.
A small "👁 view only · edit from the section page" ribbon shows for admins.

Card-expander click handler skips clicks on `.editable, .editable-input, .editable-row,
.tt-editor, .ProseMirror, input, textarea, button, a` so editing on un-expanded
cards works without expanding them.

### Auth & cookies

- `gokulraam_session` — admin cookie. `itsdangerous`-signed, 30d.
- `gokulraam_friend_session` — museum visitor cookie. 180d, scoped to friend code.
- **Prod requires `COOKIE_SECURE=true`** on Render → cookies become `SameSite=None; Secure`
  so they work cross-origin from Pages → Render.
- `FRIEND_CODE` env on Render is the code visitors paste at `/museum/enter`.
- No raw IPs stored anywhere. Guestbook only stores SHA-256 hashes for rate-limit dedupe.

### Easter eggs

Two trigger words, listened-for globally in `EasterEggs.tsx` (mounted in Base):
- `snap` — camera flash + toast to `/photos`
- `knock` — toast to `/museum/enter`

Adding more is a one-line entry in `TRIGGERS` array. Discovery state lives in
`localStorage.egg.found` (unused for now — future "secrets" panel).

### Backend conventions

- `current_admin` dependency on all admin writes
- `museum_visitor` dependency on museum reads (admin OR friend cookie)
- Idempotent seeds: every `seed_*` function checks before inserting; safe to call every boot
- `migrate.py`'s `_COLUMN_ADDS` list is the ONLY place additive migrations live
  (idempotent via `PRAGMA table_info` check)
- Routers grouped by domain (`/api/til`, `/api/now`, `/api/photos`, etc.)
- File uploads go through `app.storage.get_storage()` so LocalDisk↔R2 is transparent

### Migrations — local dev SQLite

When adding a column: append a tuple to `_COLUMN_ADDS` in `migrate.py`. Backend
reload picks it up; tables that don't exist yet are skipped (Base.metadata.create_all
will create with the new column). For destructive schema changes, drop the
SQLite file (`rm backend/app.db`) and let seeds re-run.

### Mobile

Hamburger nav for <768px (Base.astro). Most pages use Tailwind responsive prefixes.
Mobile-specific CSS for camera roll (`clamp(280px, 56vh, …)`), 404 typer (label
wraps to its own line below 540px), photo-add form (split row collapses below 540px).

## Important paths

| Want | Location |
|---|---|
| Add a new page | `frontend/src/pages/<route>.astro` |
| Add a router | `backend/app/routers/<thing>.py` + register in `main.py` |
| Add a model | `backend/app/models.py` + maybe `migrate.py` entry |
| Change site styles | `frontend/src/styles/globals.css` (long but well-ordered) |
| Change card behavior | `frontend/src/layouts/Base.astro` (card-expander is inline JS) |
| Run scraper manually | `cd backend && .venv/bin/python -m app.scrapers.bwf` |
| Hash a password | `cd backend && .venv/bin/python -m app.tools.hashpw 'new-password'` |
| Send a "status" ping | `cd backend && .venv/bin/python scripts/status.py coding "tuning postgres"` |

## Known issues (snapshot)

- ⚠ **Render auto-deploy is stuck.** The backend on production has been on
  an old commit for ~10 pushes. `/admin/stats`, `/photos` add/upload, `/logbook`
  endpoints all 404 in prod. Frontend has been updating fine on Pages.
  Open Render dashboard → `gokulraam-backend` → Events tab → look for failed
  builds or paused auto-deploy. Most likely a build failure that auto-paused
  the integration.
- 🟡 Uploaded photos vanish on Render redeploy (ephemeral disk). Workaround:
  paste URLs. Fix: add a card → R2 env vars → storage abstraction switches.

## Common pitfalls already encountered

| Symptom | Cause | Fix |
|---|---|---|
| "Invalid hook call" in SSR logs | @astrojs/react sniffer calls components as plain functions | Filtered in Base.astro (look for `__astroReactHookFilter`) — harmless |
| Save/cancel in expanded card does nothing | Clone's React hydrates fresh, edit state desyncs | CSS disables editing inside `.card-clone` |
| Cookie not sent on prod | Cross-origin Pages → Render | `COOKIE_SECURE=true` on Render |
| Bash glob breaks on `[...slug]` | zsh expands brackets | Quote the path |
| Shift+click meant as easter egg | Browser always opens new tab on shift+click of anchor | Switched to keyword trigger (`snap`) |
| Hooks-rule warning | Hook after early return | Move hooks above any `return` |
| `/photos` shows old empties | Seed only re-runs if all rows are empty | `rm backend/app.db` to fully reseed |

## Tone for replies

User prefers terse responses, code-level specifics with file:line refs, no
trailing summary paragraphs unless asked. When something is uncertain, say so.
Verify before recommending — run commands, hit endpoints, don't assume.

## When in doubt

1. Read `SPEC.md` for "what should this look like / how should it behave"
2. Read `ROADMAP.md` changelog for "when did we ship X"
3. `git log --oneline -20` for "what happened recently"
4. `grep -rn "<symbol>" backend/app frontend/src` to trace a name
