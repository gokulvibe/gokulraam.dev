# gokulraam.dev — Roadmap

> Phased plan from foundation to launch. Status updated as work lands.
> See [SPEC.md](./SPEC.md) for the product spec this implements.
> See [DEPLOY.md](./DEPLOY.md) for the production walkthrough.

---

## Current state (snapshot · 2026-06-01)

**Live in production**:
- Frontend: https://gokulraam-dev.pages.dev (Cloudflare Pages, auto-deploy from `main`)
- Backend: https://gokulraam-backend.onrender.com (Render free, auto-deploy from `main`)
- DB: Neon Postgres (free tier, pooled connection)
- Files: LocalDiskStorage on Render *(ephemeral — wiped on redeploy; R2 ready when card available)*

**Site has 14 routes**, every page is admin-editable in place. Two themes (dark "Nocturnal" / light "Daylight"). Hamburger nav on mobile. Easter eggs (`snap`, `knock`). Friends-only museum (cookie + admin-set code).

**Known issues** (open):
- ⚠ **Render backend deploy is stuck on old code.** Frontend has updated through many commits; backend hasn't picked up any push for the last ~10 commits. `/admin/stats`, `/photos` add/upload/delete, `/logbook`, the new `/api/stats/*` endpoints, the OG image generator — **all missing in production**. User needs to open Render dashboard → Events → see failing build / re-enable auto-deploy / manual deploy.
- 🟡 Uploaded photos vanish on every Render redeploy (filesystem is ephemeral). Workaround: paste external URLs. Proper fix: switch storage to R2 (code is ready; needs a card).
- 🟡 `/admin/stats` dashboard density not mobile-audited.

**Not yet built** (deliberate):
- Multi-tenant SaaS mode (Phase 7+ in this doc)
- Email/SMS notifications, password reset, account management
- A unit/integration test suite
- Site-wide search beyond ⌘K

---

## Status legend
- ✅ shipped
- 🚧 in progress
- ⏳ planned
- ❓ open decision (blocks the item)

---

## Phase 0 — Foundation ✅

- ✅ Project structure (`frontend/`, `backend/`, Makefile)
- ✅ Astro 4 (hybrid output) + Tailwind + MDX
- ✅ FastAPI + Pydantic v2 + SQLAlchemy 2 + APScheduler
- ✅ SQLite (dev), Postgres (prod) — DATABASE_URL switch
- ✅ Idempotent schema migrator (`app/migrate.py`) for additive column changes
- ✅ Resume PDF at `frontend/public/resume.pdf`
- ✅ Python 3.12 venv, `/api/health` heartbeat

## Phase 1 — Static portfolio v1 ✅

- ✅ "Nocturnal Collector's Folio" design system, dark TCG-folio aesthetic
- ✅ Fraunces + JetBrains Mono via Google Fonts
- ✅ `<ExpandableCard>` FLIP click-to-expand → 92vw × 92vh modal
- ✅ Atmosphere layers (aurora, grain, grid veil)
- ✅ Per-card accent stripe + giant watermark + numerology stamp
- ✅ 3D mouse tilt + cursor-following foil
- ✅ Homepage cards: hero (001), Now (002), TIL (003), Work (004), Uses (005), Projects (006), Badminton (007)
- ✅ Pages: `/work`, `/projects`, `/til`, `/til/<slug>`, `/now`, `/badminton`, `/uses`, `/resume`, `/resume.pdf`

## Phase 2 — Admin CMS ✅

**Sub-phases 2.0 through 2.8** — built up a full admin shell, replaced separate-page editor with the Jira-style inline editing convention (SPEC §5). Every editable surface lives on the public page and toggles to edit-in-place when admin signs in.

- ✅ bcrypt-hashed password + `itsdangerous`-signed session cookie
- ✅ `/admin/login` (only `/admin/*` route besides `/admin/stats`)
- ✅ `useIsAdmin()` hook with in-memory cache
- ✅ `<AdminBar>` floating pill at bottom-right (admin-only)
- ✅ `<EditableField>` (generic, formats: text / longtext / bullets / chips / adminOnly)
- ✅ `<EditableNowItem>`, `<EditableTitle>`, `<EditableTags>`, `<EditableBody>`, `<EditableAttachments>`, `<EditableUsesField>` — all following the same convention
- ✅ TipTap WYSIWYG editor with markdown round-trip, image/link/code-block extensions
- ✅ ⌘S to save, autosave to localStorage, navigate-confirm with unsaved changes
- ✅ Every editable section back-fills:
  - TIL post: title / tags / body / attachments / draft toggle / delete
  - /now: 9 facets (building, at-work, reading, watching, listening, learning, playing, following, headline)
  - /uses: 32 items across 7 categories (code, runtime, hardware, sound, court, fitness, daily)
  - /badminton: 4 players + 4 tournaments + admin scrape trigger
  - /work: roles, awards, certs, education (all CRUD)
  - /projects: full project list
  - Profile + ProfileStat + SpecialtyItem (hero card)
  - Museum exhibits (friends-only)
  - Books (legacy; route dropped from public)
  - Photos (URL + upload + caption + date)
  - Logbook entries
- ✅ Cross-island save sync via CustomEvent so expanded-card clones stay in sync
- ✅ Cross-origin auth: cookies `SameSite=None; Secure` in prod (gated on `COOKIE_SECURE` env)
- ✅ SSR draft fallback (`TilDraftLoader`) for cross-origin browsing

## Phase 3 — Live badminton data ✅

- ✅ `BadmintonMatch` model + structured `start_date`/`end_date` columns
- ✅ tournamentsoftware.com scraper (`backend/app/scrapers/bwf.py`)
- ✅ YAML fallback (`backend/data/badminton.yaml`)
- ✅ Daily APScheduler cron at 06:00 local
- ✅ `/api/badminton/players` + `/api/badminton/tournaments` endpoints
- ✅ Admin-trigger endpoint to run scrape on demand
- ⏳ `/api/badminton/upcoming` — composite endpoint with cached scrape results (deferred; not blocking)

## Phase 4 — Analytics & signal ✅

- ✅ Page view tracking via `<script>` in Base.astro → `POST /api/stats/track`
- ✅ `/admin/stats` dashboard — summary tiles, daily chart, top paths, top referrers, recent feed
- ✅ Admin self-views flagged (`page_views.is_admin`) and excluded from counts
- ✅ RSS feed at `/til/rss.xml` (auto-discovery via `<link rel=alternate>`)
- ✅ OpenGraph image generator at `/api/og/til/<slug>.png` (1200×630 PNG via Pillow)
- ✅ Per-TIL share panel: preview image, copy link, download PNG
- ✅ ⌘K fuzzy search — `/api/search` aggregator across every editable surface
- ✅ Live "currently" status (`StatusPing` model + `/api/status` + `scripts/status.py` CLI)
- ⏳ GitHub commit graph on homepage — decided not needed (user doesn't commit from personal repo often)
- ⏳ Spotify "now playing" widget — deferred (needs OAuth setup)

## Phase 5 — Deployment ✅

**Done**:
- ✅ Cloudflare Pages (frontend) + Render (backend) + Neon Postgres
- ✅ Cross-origin cookies (`SameSite=None; Secure` in prod via `COOKIE_SECURE=true`)
- ✅ `render.yaml` Blueprint, `wrangler.toml`, `.assetsignore` for Workers Builds
- ✅ `astro.config.mjs` defaults to Cloudflare adapter, Node available via `ASTRO_ADAPTER=node`
- ✅ Storage abstraction (`app/storage.py`) — switches LocalDisk ↔ R2 by env var
- ✅ Cross-site CORS + cookie config
- ✅ `passthroughImageService()` (no Sharp on Workers)

**Pending** (user actions, deferred until they have a card / domain):
- ⏳ Cloudflare R2 bucket (10 GB free) — `app/storage.py` already supports it; just needs env vars
- ⏳ Custom domain `gokulraam.dev` at Cloudflare Registrar
- ⏳ Fix the current Render auto-deploy stall (see "Known issues" above)

---

## Phase 6 — Community & content ✅

- ✅ Guestbook (`/guestbook`) — anonymous, honeypot + IP-hash rate limit, admin soft-hide
- ✅ Photo log (`/photos`) — camera-roll layout with film-strip sprockets, lightbox, sample picsum seeds, admin add (URL or upload), delete
- ✅ Logbook (`/logbook`) — short-form observations grouped by day, tag pills, compose form (admin)
- ✅ Museum (`/museum`) — friends-only six-room exhibit, gated by `FRIEND_CODE` env + 180-day cookie
- ✅ Light "Daylight" theme — full light palette, no-flash pre-paint script, theme toggle persisted
- ✅ Casual home for non-dev visitors (profile.casual_about + casual_interests editable)
- ✅ AmbientPlayer (light-theme only ambient track button)
- ✅ Custom 404 page with destination card grid + type-to-go input + small puzzle (click digits 4-0-4)
- ✅ Easter eggs — type `snap` → camera flash + photos toast; type `knock` → museum entry toast
- ✅ Mobile sweep — hamburger nav, hero font scaling, camera-roll frame heights, lightbox padding, photo-add form column collapse, 404 typer wrapping
- ❌ Bookshelf — built then dropped (user doesn't read many books; route removed, table kept)

---

## Phase 7+ — Multi-tenant platform 🌱 *(not started)*

> Full architecture in [SPEC §10](./SPEC.md#10-future-vision--multi-tenant-mode-).
> Goal: any visitor signs up, gets a seeded copy of this template, edits everything,
> publishes to a custom domain.

### Schema migration (when this lands)
- ⏳ `User` table (email, password_hash, created_at, plan)
- ⏳ `Site` table (id, owner_id, slug, custom_domain, brand_colors, is_published)
- ⏳ Add `site_id INT NOT NULL FK Site.id` to every content table
- ⏳ Backfill existing rows to `site_id=1` (Gokul's site)
- ⏳ Multi-user auth; sessions carry `user_id`
- ⏳ Middleware: resolve `current_site` from host header / subdomain / path

### Auth & accounts
- ⏳ `/signup` + email verification
- ⏳ Password reset flow
- ⏳ Account settings (change password, delete account)

### Site management
- ⏳ Per-user dashboard / inline editing of their own site
- ⏳ Publish/unpublish toggle
- ⏳ Custom-domain config UI + Caddy on-demand TLS
- ⏳ Per-site upload partitioning + free-tier subdomain (`<slug>.gokulraam.dev`)
- ⏳ Onboarding: seed each new site with placeholder content

### Out of scope for v1 (when multi-tenant lands)
- Multi-author per site (single owner only)
- Real-time collaborative editing
- Site templates / themes other than this one
- White-label (every site says "powered by")

---

## Easter eggs — registered triggers

Quick reference so I don't forget what's there. Source of truth lives
in `frontend/src/components/EasterEggs.tsx`.

| # | Trigger | What it does | Reveals |
|---|---|---|---|
| 1 | Type `snap` anywhere (desktop) | camera-flash overlay + toast | `/photos` |
| 2 | Type `knock` anywhere (desktop) | page rumble + 3 audio thumps + haptic buzz + toast | `/museum/enter` |
| 3 | Tap **3 times** anywhere on the page (mobile-friendly) | same as `snap` — after a 700ms pause | `/photos` |
| 4 | Tap **5 times** anywhere on the page | same as `knock` — after a 700ms pause | `/museum/enter` |
| 5 | On `/404`, click the digits **4 → 0 → 4** in order | digits glow gold, link cards pulse | nothing — just a playful nod |

Subtle visual hint while tapping: a small `tap · ● ● ○ ○ ○` chip
appears at the bottom of the screen after the 2nd tap so the gesture
isn't invisible.

Audio + haptic are mutable via the **SoundToggle** (♪ chip top-right
of every page). When muted, the page-shake still plays on knocks.

Discovery state is stored in `localStorage.egg.found` — wire it into a
future "secrets" panel that lists found eggs + hints undiscovered ones.

---

## Backlog (small, doable any time)

- ⏳ Real content backfill — fill `—` placeholders in `/uses`, write actual TIL posts, populate museum rooms, replace seeded sample photos with personal ones
- ⏳ Site changelog page (auto from git or hand-curated) — defer until there's an audience to read it
- ⏳ "Secrets found" panel triggered by Konami code — reveals discovered easter eggs + hints for undiscovered ones (localStorage ledger already in place)
- ⏳ Mobile pass for `/admin/stats` dense tables
- ⏳ Print stylesheet for `/resume`
- ⏳ Friend-only TIL drafts (museum-tier visibility for personal/sensitive technical posts)
- ⏳ Spotify "now playing" widget (needs OAuth)
- ⏳ Unit/integration test suite (currently zero — relying on manual + Astro build)

---

## Changelog

| Date | Change |
|---|---|
| 2026-05-28 | v0 scaffold: project structure, Astro + FastAPI |
| 2026-05-28 | v1 static portfolio: all pages, MDX-backed TIL |
| 2026-05-28 | Design overhaul: Nocturnal Folio dark theme + FLIP cards |
| 2026-05-28 | `/work` expanded with freelance, projects, certs, MG Scholarship |
| 2026-05-28 | `/uses` redesigned across 7 lifestyle categories |
| 2026-05-28 | Phase 2 shipped: admin login + TipTap editor + attachments + DB-backed TIL |
| 2026-05-28 | Phase 2.1: Jira-style inline editing + floating AdminBar |
| 2026-05-28 | Phase 2.2: SSR for /til pages, folded post mgmt into /til |
| 2026-05-28 | Phase 2.3: AdminBar stripped to chip + sign-out; publish/delete inline on `/til/<slug>` |
| 2026-05-29 | Phase 2.4: homepage SSR + /now editable inline (first non-TIL editable) |
| 2026-05-29 | Phase 2.5: /uses editable inline (32 items, name + note) |
| 2026-05-29 | Phase 2.6: /badminton + homepage card editable; generic `<EditableField>` introduced |
| 2026-05-29 | Phase 2.7: /work + /projects editable; EditableField formats text/bullets/chips/longtext |
| 2026-05-29 | Phase 2.8: Profile + ProfileStat + SpecialtyItem; **every page is now admin-editable** |
| 2026-05-31 | Phase 4.1: RSS at `/til/rss.xml` |
| 2026-05-31 | Phase 4.2: OG image generator `/api/og/til/<slug>.png` (Pillow + font fallback) |
| 2026-05-31 | Phase 4.3: ⌘K fuzzy search — backend aggregator + global React modal |
| 2026-05-31 | Phase 4.4: Live "currently" status widget |
| 2026-05-31 | Phase 3: Badminton scraper + APScheduler cron + YAML fallback + migrator helper |
| 2026-05-31 | Phase 6.1: Light "Daylight" theme + theme toggle + casual home + AmbientPlayer |
| 2026-05-31 | Phase 5 (code): Render/Neon/R2 stack prepared, `app/storage.py` abstraction, `astro.config` adapter switch |
| 2026-06-01 | Production live on Cloudflare Pages + Render + Neon. Cross-site cookies working (`COOKIE_SECURE=true`). Workers Builds + `.assetsignore` configured. |
| 2026-06-01 | Museum (friends-only): `MuseumExhibit` model, 6 seeded rooms, friend cookie (`gokulraam_friend_session`, 180d), gated `museum_visitor` dependency |
| 2026-06-01 | `/admin/stats` dashboard: summary tiles, daily chart, top paths/referrers, recent feed; admin self-views excluded |
| 2026-06-01 | Guestbook live at `/guestbook` — honeypot + IP-hash rate limit |
| 2026-06-01 | Photo log: camera-roll layout, picsum samples, lightbox; followed by polaroid alternate then dropped after comparison |
| 2026-06-01 | Easter eggs: keyword triggers for `snap` (→ /photos with shutter flash) and `knock` (→ /museum). Shift-click discarded (browser hijacks for new-tab) |
| 2026-06-01 | Bookshelf built then dropped (user doesn't read many books) |
| 2026-06-01 | EditableBody polish: ⌘S to save, localStorage autosave every 5s, navigate-confirm |
| 2026-06-01 | TIL share panel: preview OG image, copy link, download PNG |
| 2026-06-01 | Custom 404 with destination cards + type-to-navigate + 4-0-4 click puzzle |
| 2026-06-01 | Logbook (`/logbook`): short-form observations grouped by day, tag pills, compose form |
| 2026-06-01 | Now categorization experiment reverted — listening/following kept as flat additions |
| 2026-06-01 | Mobile sweep: hamburger nav, hero font scaling, camera-roll heights, lightbox padding |
| 2026-06-01 | Photos add+delete (admin): create from URL or upload; 15 MB cap; whitelist of image MIMEs; on-delete file unlink for local uploads |
| 2026-06-01 | Bug fixes: card-expander stops swallowing edit clicks, cross-island save sync via CustomEvent, stopPropagation on every editable, hooks-rule fix for `adminOnly`, `@astrojs/react` SSR sniffer warning filtered |
| 2026-06-01 | Render deploy unstuck: migrator was SQLite-only (`PRAGMA table_info`) and silently no-op'd on Postgres → schema stale → crash at startup. Fixed via SQLAlchemy `Inspector` + per-dialect DDL translation. Auto-deploy was paused after failures; triggered via Render MCP. |
| 2026-06-01 | Neon connection-pool fix: `pool_pre_ping=True` + `pool_recycle=300` for Postgres to survive Neon's free-tier idle-suspend. |
| 2026-06-01 | Knock egg gains audio (WebAudio 3-thump sequence) + page rumble. |
| 2026-06-02 | Knock haptic: `navigator.vibrate([50,110,50,110,50])` synced with the audio thumps (Android-only — Apple removed Web Vibration). |
| 2026-06-02 | Easter eggs: replaced long-press / per-element triple-tap with **page-wide tap counter** (3 → photos, 5 → museum, evaluated after 700ms idle); small "tap · ● ● ●" chip appears after the 2nd tap for discoverability. Removed `/photos` from the mobile hamburger so it stays an egg-only destination. |
| 2026-06-03 | PWA: `manifest.webmanifest` + 192/512 standard & maskable PNG icons + apple-touch-icon + Apple PWA meta (`apple-mobile-web-app-capable` etc.). No service worker yet — installability only. Per-scheme `theme-color`. |
| 2026-06-03 | Sound on/off toggle (♪) next to the theme toggle. Persists to localStorage, mirrored to `<html data-sound>`. EasterEggs gates knock audio + haptic; visual page-shake always plays. |
| 2026-06-03 | Migrator gained a data-backfill scaffold (idempotent guarded UPDATEs); photos page surfaces a clear "image didn't load" overlay for non-image URLs; print stylesheet hides chrome and unfolds anchor URLs inline; admin bar gets a "🥚 eggs" reference modal. |
| 2026-06-06 | Switched to Alembic. Migrations now run as their own step (`make migrate` / Render's startCommand) — no longer fire from the FastAPI lifespan. The custom `_COLUMN_ADDS` list is retired; baseline migration calls `Base.metadata.create_all`, future changes ship as named revisions in `backend/alembic/versions/`. `app/migrate.py` is the bootstrap wrapper that handles fresh / legacy-populated / alembic-managed DBs uniformly. |
