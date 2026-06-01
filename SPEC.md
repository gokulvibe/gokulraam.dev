# gokulraam.dev — Product Specification

> A personal site that doubles as a dev portfolio for recruiters **and** a personal
> hub for Gokul Raam — backend engineer, badminton fan, learning-in-public type.
> Distinctive, refined, dark. Not a generic blog template.

---

## 1. Vision & Audiences

The site has to serve three very different audiences without feeling fragmented:

| Audience | What they care about | First thing they should see |
|---|---|---|
| Recruiters / hiring managers | Skills, experience, signal in 30 seconds | Hero card 001 — name, role, stats, CV download |
| Fellow developers | TIL notes, projects, stack, taste | `/til`, `/projects`, `/uses` |
| Friends / personal | Now, badminton, fitness, the human | `/now`, `/badminton`, `/uses` |

The hero card is built so a recruiter can absorb everything they need in one viewport
without scrolling. Other cards reveal personality on tap.

---

## 2. Aesthetic — "Nocturnal Collector's Folio"

Dark TCG-folio. Think a leather-bound collector's album opened at midnight, not a
gamer dark mode.

| Token | Value | Use |
|---|---|---|
| `void` | `#0b0b0f` | Base background |
| `smoke` / `ash` | `#16171f` / `#1d1e28` | Card surface |
| `cream` | `#e9e2cf` | Primary text |
| `parchment` | `#d8cfb6` | Body / secondary text |
| `mist` / `ghost` | `#8e8a7d` / `#5a5852` | Muted, micro-text |
| `ember` | `#ea580c` | Primary accent (metrics, links) |
| `gold` | `#c9a96e` | Card-game flourish, watermarks |
| `sage` / `rose` / `lilac` | `#5a8a7a` / `#b9472f` / `#9d88b8` | Per-card type stripes |

**Typography**
- **Fraunces** — variable serif. Display + body. Italic axis is high-SOFT for character.
- **JetBrains Mono** — labels, numerals, code, micro-meta. Always uppercase + wide tracking for labels.
- No Inter, no Roboto, no system stack.

**Atmosphere layers** (fixed, behind content)
- Two slow-drifting radial gradients (ember top-right, lilac bottom-left)
- SVG turbulence grain at 5.5% opacity, `mix-blend-mode: overlay`
- Faint 48px grid masked to viewport center

**Game-card system** — every homepage card has:
- Numerology stamp (№ 001…007) top-left
- Type-color edge stripe at the top
- Card-color tinted top gradient
- Giant italic watermark in bottom-right (4.5% opacity, card color)
- Cursor-following foil light
- 3D mouse tilt on hover
- **FLIP click-to-expand** → fills 92vw × 92vh modal, backdrop blurs, reveals detail panel
- Closes on Esc, backdrop click, or close button

---

## 3. Site Map

### Public

| Path | Card # | Section | Purpose |
|---|---|---|---|
| `/` | — | Folio home | Hero (001) fills viewport; cards 002–007 below |
| `/work` | 004 | Full chronicle | Saama + freelance + awards + selected projects + certs + education |
| `/projects` | 006 | Project catalogue | All projects with details |
| `/til` | 003 | Today I Learnt | Microblog of small lessons |
| `/til/<slug>` | — | TIL post | Single TIL with markdown body, attachments, share panel |
| `/til/rss.xml` | — | RSS | TIL feed |
| `/now` | 002 | Now | What I'm currently doing (live status + facets) |
| `/badminton` | 007 | Court diaries | Players + upcoming tournaments (scraped daily) |
| `/uses` | 005 | Uses | Code + runtime + hardware + sound + court + fitness + daily |
| `/resume` · `/resume.pdf` | — | Résumé | HTML + downloadable PDF |
| `/logbook` | — | Logbook | Short-form observations, grouped by day |
| `/photos` | — | Camera roll | Horizontal film-strip with lightbox |
| `/guestbook` | — | Guestbook | Visitors leave a note (honeypot + rate-limited) |
| `/404` | — | Not found | Card-aesthetic 404 with destination picker |

### Gated

| Path | Gate | Purpose |
|---|---|---|
| `/admin/login` | — | Admin sign-in (only `/admin/*` write surface) |
| `/admin/stats` | admin cookie | Page-view analytics — summary, daily chart, top paths/referrers, recent |
| `/museum/enter` | — | Friend-code entry form |
| `/museum` | friend OR admin cookie | Six-room exhibit (origins, court, workshop, …) — only people with the code |

### Easter eggs

Typed keywords surface paths that aren't in the nav:
- Type `snap` (anywhere outside an input) → toast linking to `/photos` + camera-flash overlay
- Type `knock` → toast linking to `/museum/enter`

---

## 4. Content Model

### TIL post
| Field | Type | Notes |
|---|---|---|
| `id` | int | PK |
| `slug` | str | auto from title, unique |
| `title` | str | 1–300 chars |
| `body_md` | text | Markdown source |
| `tags` | str | comma-separated, stored flat |
| `draft` | bool | drafts hidden from public list |
| `created_at` / `updated_at` | datetime | auto-managed |

### TIL attachment
| Field | Type | Notes |
|---|---|---|
| `post_id` | FK → til_posts | cascade delete |
| `filename` | str | original name |
| `stored_path` | str | `<post_id>-<uuid8>-<safe-name>` |
| `mime_type` | str | best-effort sniff |
| `size_bytes` | int | hard cap 10 MB |

**Rendering rules**
- `.py .sql .js .ts .go .rs .yaml .json` → inline syntax-highlighted block (Shiki)
- `.pdf .docx .md .txt` → download chip with filename + size
- `.png .jpg .webp .gif` → inline image

### Badminton (v3+)
- **Player** — `name`, `country`, `discipline` (MS/WS/MD/WD/XD), `bwf_id`
- **Tournament** — `name`, `location`, `tier`, `start_date`, `end_date`
- **Match** — `player_id`, `tournament_id`, `opponent`, `round`, `scheduled_at`

### Page view (analytics)
`path`, `referrer`, `user_agent`, `created_at`. Aggregated at `/admin/stats`.

---

## 5. Content Editing Model

**Goal**: when admin is logged in, the regular site becomes editable in place.
Visitors see a clean, static-looking site. There are **no separate `/admin/*`
pages** for content management — admin chrome layers onto the public pages.

### The single convention

Every editable field on the site is a React island following this shape:

```tsx
function Editable<X>({ entityId, initial, ...rest }) {
  const isAdmin = useIsAdmin();
  const [editing, setEditing] = useState(false);

  if (!isAdmin || !editing) {
    return <ViewMode value={initial} onClick={() => isAdmin && setEditing(true)} />;
  }
  return <EditMode value={initial} onSave={...} onCancel={...} />;
}
```

**Rules of the convention**:

1. **Each field is independent.** `useIsAdmin()` is called per-component (cached
   in-memory by `useIsAdmin.ts`). No global edit-mode toggle.
2. **View mode renders identically to the visitor's view.** The only difference
   for admin is a hover affordance (gold border + ✏ pencil chip).
3. **Click → inline edit mode.** Same DOM region, replaced with an input or
   editor. `[save] [cancel]` buttons appear directly below.
4. **Save calls a typed PATCH** on the relevant API endpoint (e.g. `PATCH /api/til/<id>`).
5. **Each field saves independently.** No "save all" — every input is autonomous.
6. **Enter saves, Escape cancels** on simple fields. Rich fields (TipTap) use
   explicit save/cancel buttons.

### Site-wide chrome — `<AdminBar>`

A floating pill, fixed bottom-right, mounted globally in `Base.astro`. Renders
**only** when authenticated. Shows the admin chip + context-aware actions:

| Page | AdminBar actions |
|---|---|
| `/` `/work` `/projects` `/now` `/badminton` `/uses` `/til` | `+ new TIL` · sign out |
| `/til/<slug>` | `+ new` · publish/unpublish · 🗑 delete · sign out |
| (future) `/now`, `/uses` | add new item · sign out |

### Backend convention

Every editable area needs:
- A SQLAlchemy model with `id`, `created_at`, `updated_at`
- A Pydantic `*Out` schema for reads
- A Pydantic `*Update` schema with all fields `Optional` (partial PATCH)
- A FastAPI router with `GET /api/<thing>`, `GET /api/<thing>/<id>`,
  `PATCH /api/<thing>/<id>`, `POST /api/<thing>`, `DELETE /api/<thing>/<id>`
- Admin-only mutation endpoints guarded by `Depends(current_admin)`

### Extending to a new editable area

When making a previously-static section editable (e.g. `/now` items), the recipe is:

1. **Backend**: add the model + schemas + router. Five endpoints.
2. **Frontend**: create one `Editable<X>` component per field type
   (`EditableNowItem`, `EditableUsesItem`…). Each follows the convention above.
3. **Page**: replace the static JSX block with the Editable component, passing
   `initial` from the SSR-fetched data and the `entityId`.
4. **AdminBar**: optionally add a contextual `+ add item` action for that page.

The TIL implementation is the reference; copy its shape.

### Page rendering rules

Pages that contain editable content must read **live data on every request** so
edits and new entities reflect immediately on refresh. In Astro:

```astro
---
export const prerender = false;  // SSR per request
const data = await fetch(`${API_BASE}/api/...`);
---
```

Otherwise the page is static and saved edits won't appear until the next build.
Pages with no editable content (`/work`, `/projects`, `/now`, `/uses`,
`/badminton`) can stay prerendered for now — when they gain editable fields,
they switch to `prerender = false`.

## 6. Auth Model

**Two cookie tiers — admin + friend.** No registration, no OAuth, no multi-tenant.

### Admin (Gokul)

- Single user. bcrypt-hashed password in `ADMIN_PASSWORD_HASH` env
- `SESSION_SECRET` signs the admin cookie (`itsdangerous`)
- Cookie: `gokulraam_session` · `httpOnly` · 30-day
- Locally: `SameSite=Lax`. Prod (cross-origin Pages → Render): `SameSite=None; Secure` — enabled by `COOKIE_SECURE=true` on Render
- `/api/auth/login` validates; `/api/auth/me` returns user; `/api/auth/logout` clears
- Admin-only routes use `Depends(current_admin)` on the FastAPI side
- Frontend `/admin/*` checks `/api/auth/me` and redirects to login on 401

### Friend (museum visitors)

- No user account — a *shared* code (`FRIEND_CODE` env on Render)
- `/api/auth/museum-enter` accepts the code, issues `gokulraam_friend_session` (180-day, signed)
- `museum_visitor` dependency accepts either an admin OR a valid friend cookie
- No identity carried — anyone with the code reads the museum content
- Light spam protection: same code, no rate limit; if leaked Gokul rotates `FRIEND_CODE`

---

## 7. Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Astro 4 (hybrid output) + Tailwind + MDX + React islands | Static for public pages, SSR for editable pages |
| SSR adapter | `@astrojs/node` (standalone) | For pages with `prerender = false`; runs alongside Astro static build |
| Backend | FastAPI + Pydantic v2 + SQLAlchemy 2 | Matches Saama work stack, type-safe, async-ready |
| Database | SQLite | Single file, zero ops, fine for personal scale |
| File storage (uploads) | Local disk (v2) → Cloudflare R2 (v3+) | Free tiers, no egress on R2 |
| Hosting — frontend | Cloudflare Pages | Free, unlimited bandwidth |
| Hosting — backend | Hetzner CX11 (~₹360/mo) or Oracle Always Free | Cheap, Python-friendly |
| Domain registrar | Cloudflare Registrar | At-cost pricing, no markup |
| Analytics | Cloudflare Web Analytics | Free, cookie-less, no consent banner |

---

## 8. Non-Goals

These are explicitly **out of scope** to keep complexity in check:

- Multi-author CMS *(today)* — only Gokul writes. Multi-tenant is a separate future direction (§10).
- User accounts, comments, social login
- E-commerce, payments
- Native mobile app or installable PWA
- Full i18n / multi-language
- Realtime collaboration
- Heavy WebGL anywhere except as optional polish

*(Light theme was once a non-goal — now shipped as the "Daylight" theme for
non-dev visitors. The Nocturnal Folio remains the canonical identity; the
toggle lives top-right, persisted in localStorage.)*

---

## 9. Performance & A11y Budget

| Metric | Target |
|---|---|
| Lighthouse Performance | ≥ 95 on `/` |
| Lighthouse Accessibility | ≥ 95 |
| LCP | < 1.5s on a 4G connection |
| First-load JS (homepage) | < 30 KB gzipped |
| Color contrast | WCAG AA on all text |
| Keyboard navigable | All interactive cards open via Enter/Space; Esc closes |
| `prefers-reduced-motion` | All animations dampened |

---

## 10. Future Vision — Multi-tenant Mode 🌱

> **Long-term direction.** Today: single-user CMS for Gokul. Tomorrow: a
> template that any visitor can sign up for, claim their own copy of, edit
> everything, and publish to their own custom domain in a few clicks.
> Think Carrd / Linktree / Notion sites, but with this Nocturnal Folio
> aesthetic and a dev-first content model (TIL, /now, /uses, projects, work).

### The product story

1. A visitor lands on `gokulraam.dev`, likes the look, clicks **"Get your own"**.
2. They sign up with email + password. A new `Site` is seeded for them with
   placeholder content (their own TIL, Now, Uses, Badminton, Work, Projects).
3. They edit everything in place — the same inline editing convention they
   see on Gokul's site, just scoped to their data.
4. They get a free subdomain (`<slug>.gokulraam.dev` or similar) immediately.
5. To go to a custom domain, they paste their domain, follow CNAME instructions,
   and click "Publish". HTTPS provisions automatically via Caddy on-demand TLS.

### Data model changes when this lands

```
+----------+      +----------+      +-----------------------+
|   User   | <--- |   Site   | ---> | TilPost, NowItem,     |
| id       | 1:N  | id       | 1:N  | UsesItem, Badminton*, |
| email    |      | owner_id |      | WorkRole, Project, …  |
| pw_hash  |      | slug     |      | + new site_id FK      |
+----------+      | domain   |      +-----------------------+
                  | published|
                  +----------+
```

- **New tables**: `User` (email, password_hash, created_at, plan)
  and `Site` (id, owner_id, slug, custom_domain nullable, brand_colors JSON,
  is_published, created_at, updated_at)
- **Every content table gains `site_id INTEGER NOT NULL FK Site.id`**:
  `til_posts`, `til_attachments`, `now_items`, `uses_items`,
  `badminton_players`, `badminton_tournaments`, plus future `work_roles`,
  `projects`, `awards`, `certifications`.
- **Every API query becomes site-scoped**: `WHERE site_id = current_site.id`.
- **Site resolution per request** (middleware):
  - host header matches a `custom_domain` → that site
  - URL is `<slug>.gokulraam.dev` → site by slug
  - URL is `gokulraam.dev/sites/<slug>` (fallback before custom domain) → site by slug
  - URL is `gokulraam.dev` itself → Gokul's site (id=1)

### Migration path from today's single-tenant DB

This is a one-time migration, scriptable:

1. Add `User` + `Site` tables.
2. Insert seed user (Gokul) and Site (id=1, slug=`gokulraam`, owner_id=1).
3. `ALTER TABLE ... ADD COLUMN site_id INTEGER DEFAULT 1` on every content table.
4. Backfill any existing rows to `site_id = 1`.
5. Make `site_id` NOT NULL, add FK.
6. Update API routers to filter by `current_site.id` via a `Depends`.
7. Update `current_admin` to return the `User`, and resolve their site.

### Infrastructure additions needed

- **Custom domain TLS**: Caddy with `on_demand` TLS issuance — automatic Let's Encrypt
  certs on first request to a verified domain. Alternative: Cloudflare for SaaS.
- **DNS guidance UI**: shows the user what CNAME / A record to add at their registrar.
- **Per-site upload isolation**: `backend/data/uploads/<site_id>/...` so files don't
  collide and quotas are easy to enforce.
- **Publish/unpublish toggle**: `Site.is_published` flag. Unpublished sites return
  404 on their public URL but stay editable in the dashboard.
- **Plan limits** (optional, later): max posts, max storage, max custom domains.

### What today's design already enables

These choices we've already made are forward-compatible — no changes needed:

- ✅ **Editable convention (SPEC §5)**: each `Editable*` component takes an entity
  id and PATCHes a typed endpoint. When `site_id` lands, scoping happens at the
  backend level — components don't need to change.
- ✅ **REST endpoints organised by entity** (`/api/til/<id>`, `/api/now/<slug>`,
  `/api/uses/<id>`): adding a `site_id` filter is a single middleware concern.
- ✅ **`/admin/login` is the only admin route**: when we switch to multi-user,
  it becomes `/login` and handles registration too.
- ✅ **Astro per-request rendering**: each SSR page resolves "current site" from
  the host header once at the top, then renders normally. Single-tenant for
  the user, multi-tenant for the platform.
- ✅ **Static section chrome** (category titles, glyphs in `/uses`; player flags
  in `/badminton`): structured per-row data with editable fields is multi-tenant
  friendly. Hardcoded design copy stays in code.

### Things that need to change

- `seed.py` becomes per-user-on-signup instead of per-server-on-boot.
- `current_admin` resolves to a `User`, not just a username; rights checks become
  ownership checks (`user.id == site.owner_id`).
- `/api/auth/*` adds registration, email verification, password reset.
- AdminBar shows "switch site" when a user owns multiple (e.g., portfolio + side project).
- Hardcoded `ADMIN_USERNAME` env var goes away; replaced by DB users.

### What we *won't* do (to keep complexity bounded)

- Multi-author per site (single owner only)
- Real-time collaborative editing
- Site templates / themes other than this one (single aesthetic for v1)
- White-label (every site is "powered by" the platform brand)
- Migration tools for users to move their content to a self-hosted backend

## 11. Open Decisions

Resolved decisions (recorded for posterity; no longer open):
- ✅ **Domain** — `gokulraam.dev` (Cloudflare Registrar planned; not yet purchased)
- ✅ **Backend host** — Render free tier (paired with Neon Postgres + R2 for files)
- ✅ **Badminton data source** — tournamentsoftware.com scraper with YAML fallback
- ✅ **Editor library** — TipTap (ProseMirror) with `tiptap-markdown` for round-trip

Still open:
- **R2 vs ephemeral disk for prod uploads** — code switches automatically when
  `R2_*` env vars are set. Currently on ephemeral disk (no card on file).
  Uploaded photos vanish on every Render redeploy.
- **Custom domain purchase** — deferred until ready to pay (~₹1.5k/yr).
- **Multi-tenant timing** — §10 spec is ready; no commitment yet.
