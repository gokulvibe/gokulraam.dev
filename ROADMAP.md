# gokulraam.dev — Roadmap

> Phased plan from foundation to launch. Status updated as work lands.
> See [SPEC.md](./SPEC.md) for the product spec this implements.

## Status legend
- ✅ shipped
- 🚧 in progress
- ⏳ planned
- ❓ open decision (blocks the item)

---

## Phase 0 — Foundation ✅ *(complete)*

- ✅ Project structure (`frontend/`, `backend/`, Makefile)
- ✅ Astro 4 scaffold with Tailwind + MDX integrations
- ✅ FastAPI scaffold with SQLAlchemy 2 + Pydantic v2
- ✅ SQLite database with `TilPost`, `TilAttachment`, `PageView` models
- ✅ `.env.example` + `app/tools/hashpw.py` admin password helper
- ✅ Resume PDF copied into `frontend/public/resume.pdf`
- ✅ Python 3.12 venv, npm install paths
- ✅ Backend health check at `/api/health`

## Phase 1 — Static portfolio v1 ✅ *(complete)*

### Aesthetic
- ✅ "Nocturnal Collector's Folio" design system locked in
- ✅ Fraunces + JetBrains Mono via Google Fonts
- ✅ Dark palette (`void`, `smoke`, `cream`, `ember`, `gold` …)
- ✅ Atmosphere layers (aurora drift, grain, grid veil)

### Card system
- ✅ `<ExpandableCard>` component with face + detail slots
- ✅ FLIP click-to-expand animation, 92vw × 92vh modal
- ✅ Backdrop blur, scroll lock, Esc/click-outside/close-button to dismiss
- ✅ Cursor-following foil, 3D mouse tilt
- ✅ Per-card accent stripe + giant watermark + numerology
- ✅ Hero variant fills first viewport
- ✅ Clear English titles + italic kickers on every card
- ✅ Floating "specialties" grid in hero detail (replaced bullet duplication)
- ✅ "Continue the folio" scroll cue + section divider

### Pages
- ✅ `/` — hero + 6 cards (Now, TIL, Work, Uses, Projects, Badminton)
- ✅ `/work` — full chronicle (Saama × 2 + freelance + awards + selected projects + certs + education)
- ✅ `/projects` — full catalogue
- ✅ `/til` — index + `/til/<slug>` single post (reads from MDX content collection)
- ✅ `/now` — what I'm currently doing
- ✅ `/badminton` — players (Lakshya, Lee Zii Jia, Satwik–Chirag, Shi Yu Qi) + tournaments
- ✅ `/uses` — 7 categories: code, runtime, hardware, sound, court, fitness, daily
- ✅ `/resume` — HTML version + PDF download

---

## Phase 2 — TIL admin ✅ *(complete)*

**Goal**: Gokul can write/edit/delete TIL posts from the UI with attachment support,
behind login. Frontend reads from backend.

### Backend wiring
- ✅ Switch `/til` index + `/til/[...slug]` to fetch from `/api/til` at build time
- ✅ Render attachments per type: code inline, images inline, others as download chips
- ✅ Seed module imports existing MDX TILs into DB on first boot
- ✅ `stored_path` exposed in attachment schema for direct file URLs
- ✅ `bcrypt<4.1` pinned to fix passlib compat
- ✅ `.env` with bcrypt-hashed admin password

### Admin shell
- ✅ `AdminLayout.astro` with global logout button
- ✅ `/admin/login` — React `LoginForm` posts to `/api/auth/login`
- ✅ `/admin` — `AuthGate` + `PostList` showing drafts and published with edit/delete
- ✅ Cookie-based auth guard (redirects to `/admin/login` on 401)
- ✅ Logout works site-wide from header

### Editor (`/admin/til/new` and `/admin/til/edit?id=`)
- ✅ TipTap (ProseMirror) WYSIWYG editor — same engine as Confluence
- ✅ `tiptap-markdown` extension — saves/loads as markdown round-trip
- ✅ Toolbar: H1/H2/H3, bold, italic, strike, bullet list, ordered list, quote, inline code, code block, link, image, horizontal rule, undo, redo
- ✅ Title field + tags field (comma-separated)
- ✅ Drag-and-drop attachment dropzone → POSTs to `/api/til/<id>/attachments`
- ✅ Attachment list shows filename + size + mime
- ✅ Draft / Publish toggle with save buttons
- ✅ Status indicator ("saving…", "saved · time", "save failed")
- ✅ Auto-saves draft before first upload (so attachments can attach to a real post)

### Polish (deferred to a later sub-phase)
- ⏳ Keyboard shortcut: ⌘S to save draft, ⌘⇧P to publish
- ⏳ Autosave drafts every 10s to localStorage
- ⏳ Confirm before navigating away with unsaved changes
- ✅ Attachment delete buttons (inline on the post page)

### Phase 2.1 — Jira-style inline editing ✅ *(complete)*

Replaced separate-page editor with click-to-edit fields on `/til/<slug>`.

- ✅ `<AdminBar>` floating pill, bottom-right, on every page (auth-aware)
  - Shows `admin · gokul` chip with pulsing dot
  - Contextual actions: `+ new`, `publish/unpublish`, `🗑 delete` (on TIL pages), `posts`, sign out
- ✅ `useIsAdmin()` hook with in-memory cache (one `/api/auth/me` fetch per page load)
- ✅ `<EditableTitle>` — click title to edit inline, Enter/Esc to save/cancel
- ✅ `<EditableTags>` — click chips, edit as comma-separated, parse on save
- ✅ `<EditableBody>` — click rendered body, TipTap toolbar appears, save/cancel
- ✅ `<EditableAttachments>` — dropzone visible only to admin, per-file remove buttons
- ✅ Backend `DELETE /api/til/attachments/<id>` endpoint
- ✅ `+ new` → POSTs draft → navigates to `/til/<slug>?new=1` → title auto-opens for edit
- ✅ Title edits that change the slug update the URL via `history.replaceState`
- ✅ Removed `/admin/til/new`, `/admin/til/edit`, `TilEditor.tsx`, `EditMount.tsx`, `AttachmentDropzone.tsx`
- ✅ `/admin` post list still works as overview; "edit" link now navigates to `/til/<slug>`

### Phase 2.2 — SSR + folded /til hub ✅ *(complete)*

Fixed the "edits aren't persisting" feel (data was saving, but stale build was rendering)
and removed the last separate-page admin friction.

- ✅ Installed `@astrojs/node` adapter, switched Astro to `output: 'hybrid'`
- ✅ `/til/[...slug]` set to `prerender = false` — fetches live from API every request
- ✅ `/til` index also `prerender = false` — drafts and edits visible immediately
- ✅ Slug-page now resolves any post that exists in the DB (no rebuild needed for new posts)
- ✅ Drafts section + `+ new entry` button rendered inline on `/til` when admin
- ✅ Per-row `delete` action appears next to published posts when admin
- ✅ Removed `/admin` (post list) page entirely
- ✅ Removed `AdminLayout.astro`, `PostList.tsx`, `AuthGate.tsx`
- ✅ `AdminBar` no longer shows a "posts" link
- ✅ `/admin/login` is the only remaining `/admin/*` route — only place to sign in
- ✅ Documented the "Content Editing Model" convention in [SPEC.md §5](./SPEC.md#5-content-editing-model)
  so future editable fields (now/uses/badminton/work bullets) follow the same shape

---

## Phase 3 — Live badminton data ⏳

**Goal**: replace static tournament + player lists with real scraped data.

- ❓ Decide source: tournamentsoftware.com scraper (recommended) vs SofaScore API
- ⏳ Add `Player`, `Tournament`, `Match` SQLAlchemy models
- ⏳ Scraper module (`backend/app/scrapers/bwf.py`) — parses draw pages with BeautifulSoup
- ⏳ Daily cron via `apscheduler` (FastAPI startup task)
- ⏳ Fallback to `backend/data/badminton.yaml` if scrape fails
- ⏳ `/api/badminton/upcoming` returns real tournaments
- ⏳ `/api/badminton/players/<id>/matches` returns upcoming matches per player
- ⏳ Frontend swaps homepage card 007 + `/badminton` page to fetch from API
- ⏳ Last-updated timestamp on the badminton page

---

## Phase 4 — Analytics & live signal ⏳

- ⏳ Page view tracking — small `<script>` in Base.astro POSTs to `/api/stats/track`
- ⏳ `/admin/stats` dashboard — top paths, daily views, referrers
- ⏳ GitHub activity strip on homepage — fetches recent commits via GitHub API at build time
- ⏳ RSS feed for `/til` (`/til/rss.xml`)
- ⏳ Sitemap verification (already in Astro config)
- ⏳ OpenGraph image generator for TIL posts
- ⏳ Optional: Spotify "now playing" widget on `/now`

---

## Phase 5 — Deployment ⏳ *(code-ready; awaiting dashboard steps in [DEPLOY.md](./DEPLOY.md))*

**Target stack**: Render Free (backend) · Neon Postgres free · Cloudflare R2 (uploads) · Cloudflare Pages (frontend). Total cost: ₹0/mo + optional domain.

### Code & config (done)
- ✅ `psycopg2-binary` added to requirements; SQLAlchemy auto-picks Postgres from `DATABASE_URL`
- ✅ `app/storage.py` — pluggable LocalDisk/R2 storage; R2 selected automatically when env vars are set
- ✅ TIL upload/delete + `/uploads/<path>` endpoint use the storage abstraction
- ✅ `@astrojs/cloudflare` adapter added; `astro.config.mjs` switches at build time via `CF_PAGES=1`
- ✅ `render.yaml` Blueprint
- ✅ `backend/.env.production.example` documents every required env var
- ✅ `frontend/wrangler.toml` notes for Pages
- ✅ `DEPLOY.md` step-by-step walkthrough (Neon → R2 → Render → Pages → CORS → smoke test → custom domain)

### Dashboard steps (you)


- ✅ **Backend host decision** — Render Free chosen (paired with Neon Postgres for persistence and R2 for files)
- ❓ **Domain decision** — `gokulraam.dev` recommended (~₹1.5k/yr at Cloudflare)
- ⏳ Buy domain at Cloudflare Registrar
- ⏳ Connect GitHub repo to Cloudflare Pages → auto-deploy on push to `main`
- ⏳ Spin up VPS or Oracle compute
- ⏳ Dockerize backend (`Dockerfile` + `docker-compose.yml`)
- ⏳ Caddy reverse proxy for free auto-HTTPS
- ⏳ systemd service for backend (or docker-compose with restart policy)
- ⏳ Set production env vars (ADMIN_PASSWORD_HASH, SESSION_SECRET, FRONTEND_ORIGIN)
- ⏳ Cloudflare Web Analytics snippet on the site
- ⏳ Backup strategy — nightly SQLite dump → R2 or backup VPS
- ⏳ Migrate attachments from local disk → Cloudflare R2 (10 GB free)
- ⏳ Smoke test all routes from prod URL
- ⏳ Submit sitemap to Google Search Console

---

## Phase 7+ — Multi-tenant platform ⏳ *(future, big)*

> See [SPEC §10](./SPEC.md#10-future-vision--multi-tenant-mode-) for the full architecture.
>
> **Goal**: any visitor can sign up, get a seeded copy of this template, edit
> everything, and publish to their own custom domain.

### Schema migration
- ⏳ Add `User` table (email, password_hash, created_at, plan)
- ⏳ Add `Site` table (id, owner_id, slug, custom_domain, brand_colors, is_published)
- ⏳ Add `site_id` FK to every content table (TilPost, NowItem, UsesItem,
  BadmintonPlayer, BadmintonTournament, plus future work/projects/awards/certs)
- ⏳ Backfill existing rows to `site_id=1` (Gokul's site)
- ⏳ Replace single-user auth with multi-user; sessions carry `user_id`
- ⏳ Middleware: resolve `current_site` from host header / subdomain / path

### Auth & accounts
- ⏳ `/signup` page (email + password)
- ⏳ Email verification (transactional email provider — Resend/Postmark)
- ⏳ Password reset flow
- ⏳ Account settings page (change password, delete account)
- ⏳ `current_admin` becomes `current_user`; ownership checks replace fixed-username checks

### Site management
- ⏳ Per-user dashboard (or just inline editing of their own site)
- ⏳ Publish/unpublish toggle (`Site.is_published`)
- ⏳ Custom-domain config UI with CNAME/A-record instructions
- ⏳ Caddy on-demand TLS for automatic HTTPS on custom domains
- ⏳ Per-site upload partitioning (`backend/data/uploads/<site_id>/...`)
- ⏳ Free-tier subdomain (`<slug>.gokulraam.dev`)
- ⏳ Onboarding: seed new user's site with default placeholder content

### Optional / nice-to-have
- ⏳ Per-site theme customization (palette swap, hero name, font choice)
- ⏳ Plan limits (max posts, max storage, custom-domain count)
- ⏳ Billing integration (Stripe — paid tier for custom domains?)
- ⏳ "Powered by gokulraam.dev" footer toggle

---

## Phase 6 — Nice-to-haves ⏳

- ⏳ Guestbook (`/guestbook` — visitors leave a note, single-table SQLite)
- ⏳ Bookshelf page (`/reading` — current + finished books)
- ⏳ Photo log (`/photos` — minimal masonry grid)
- ⏳ Three.js / WebGL hero variant (optional, only if it adds personality)
- ⏳ Light theme toggle (low priority — dark is the identity)
- ⏳ Print stylesheet for the resume page
- ⏳ Replace remaining `—` placeholders in `/uses` with real items

---

## Recent changes log

| Date | Change |
|---|---|
| 2026-05-28 | v0 scaffold: project structure, Astro + FastAPI |
| 2026-05-28 | v1 static portfolio: all pages, MDX-backed TIL |
| 2026-05-28 | Design overhaul: Nocturnal Folio dark theme + FLIP cards |
| 2026-05-28 | Hero card fills viewport; clear titles on each card |
| 2026-05-28 | Specialties floating grid replaces bullet duplication in 001 |
| 2026-05-28 | `/work` expanded with freelance, projects, certs, MG Scholarship |
| 2026-05-28 | `/uses` redesigned across 7 lifestyle categories |
| 2026-05-28 | Spec + roadmap documents added |
| 2026-05-28 | Phase 2 shipped: admin login + TipTap WYSIWYG editor + attachments + DB-backed TIL |
| 2026-05-28 | Phase 2.1: replaced separate-page editor with Jira-style inline editing + floating AdminBar |
| 2026-05-28 | Phase 2.2: SSR for /til pages (fresh data on every request), folded post mgmt into /til, deleted /admin index, documented editing convention in SPEC |
| 2026-05-28 | Phase 2.3: stripped AdminBar to chip+sign-out, moved publish/delete inline into /til/[slug], added quick-publish on draft rows, secured drafts from unauthenticated access |
| 2026-05-29 | Phase 2.4: homepage SSR (latest TIL on card), /now items editable inline (headline + 6 facets), first non-TIL field to follow the SPEC editing convention |
| 2026-05-29 | Phase 2.5: /uses items editable inline (32 items across 7 categories, name + note both editable) |
| 2026-05-29 | Phase 2.6: /badminton + homepage card editable (4 players + 4 tournaments). Introduced generic <EditableField> component. Documented multi-tenant vision (SPEC §10 + ROADMAP Phase 7+). |
| 2026-05-29 | Phase 2.7: /work + /projects editable. 4 work_roles + 3 awards + 5 certs + 1 education + 4 projects (2 featured). EditableField extended with format='bullets'\|'chips'\|'longtext' for structured display. Homepage Work/Projects cards refactored to read from DB. |
| 2026-05-29 | Phase 2.8: Profile + ProfileStat + SpecialtyItem tables. Homepage hero card 001 (face + detail) and /resume fully editable. **Every page on the site is now admin-editable.** |
| 2026-05-31 | Phase 4.1: RSS feed at /til/rss.xml (auto-discovery via <link rel=alternate>). |
| 2026-05-31 | Phase 4.2: OpenGraph image generator (/api/og/til/<slug>.png) — 1200×630 PNGs for share previews. Pillow + font-fallback chain. |
| 2026-05-31 | Phase 4.3: cmd+k fuzzy search modal — backend /api/search aggregator over every editable surface; global React island with keyboard nav. |
| 2026-05-31 | Phase 4.4: Live "currently" status — StatusPing model + POST/GET endpoints, /now card widget, scripts/status.py CLI client. |
| 2026-05-31 | Phase 3: Badminton scraper foundation — BadmintonMatch model, structured start/end dates, tournamentsoftware.com scraper, YAML fallback, daily APScheduler cron. Migrator helper for ALTER TABLE additions. |
| 2026-05-31 | Phase 6.1: Light "Daylight" theme. Theme toggle (☼/☾) top-right, persisted in localStorage with no-flash pre-paint script. CSS variables drive both palettes. Casual home: minimal typographic landing for non-dev visitors (family/friends/elders). Profile.casual_about + casual_interests editable inline. AmbientPlayer for /audio/ambient.mp3. Footer adds ⌘K hint + rss link. |
| 2026-05-31 | Phase 5 (code): production-deploy prep — psycopg2 + Postgres support, app/storage.py pluggable LocalDisk/R2 abstraction, Cloudflare adapter, render.yaml, .env.production.example, DEPLOY.md walkthrough. Dashboard steps pending. |
