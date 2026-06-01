# Deploying gokulraam.dev

> **Target stack** — all free-tier, no card required at signup:
> - **Backend** (FastAPI): Render Free
> - **Database**: Neon Postgres free
> - **File uploads**: Cloudflare R2 free
> - **Frontend** (Astro hybrid): Cloudflare Pages
>
> **Cost**: ₹0/mo + (optional later) ~₹850–1500/yr for a custom domain.
>
> **Free-tier caveats you'll see**:
> - Render free-tier backend cold-starts after 15 min idle (~30s first request)
> - Render free disk is ephemeral — that's *why* we use Neon + R2 for state
> - Neon free tier has 3 GB storage and auto-suspends idle compute
> - Cloudflare R2 free is 10 GB / 1M Class A ops / 10M Class B ops monthly

Migration path if you outgrow this is easy (host-agnostic Postgres + R2 keeps
everything portable). See [README §migration](#migrating-to-a-paid-host-later)
at the bottom.

---

## Prereqs (one-time)

You'll create accounts on:
1. **GitHub** — already done (`gokulvibe/gokulraam.dev`).
2. **Cloudflare** — for Pages, R2, and (later) the domain registrar. Sign up at https://dash.cloudflare.com/sign-up. Email + password; no card to create the account.
3. **Neon** — for Postgres. Sign up at https://console.neon.tech. You can sign up with GitHub (no card).
4. **Render** — for the backend. Sign up at https://dashboard.render.com. Sign in with GitHub (no card for free tier).

Each of these takes 2-3 min. Do them in any order.

---

## Step 1 — Neon Postgres

1. https://console.neon.tech → **New Project** → name it `gokulraam`. Region: pick closest (Singapore or Mumbai if available).
2. After creation you land on a screen with a **"Connection string"** dropdown. Pick **"Pooled connection"** (important — it works better with serverless backends).
3. Copy the URL — it looks like:
   ```
   postgresql://user:pass@ep-xxx-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
   **Save this somewhere safe.** You'll paste it into Render in a minute.

> Why pooled: Render serverless restarts open lots of brief connections. Neon's pooler keeps them efficient.

---

## Step 2 — Cloudflare R2 bucket *(optional — skip if you don't want to add a card right now)*

> **Note**: Cloudflare R2 now asks for a card on file at signup for ID
> verification (they won't charge within the free 10 GB / 1M / 10M ops tier).
> If you'd rather not add a card right now, **skip this step entirely**:
>
> - **Do not** set any `R2_*` env vars on Render in Step 3
> - The backend will auto-fall-back to local-disk storage
> - TIL post text + all other editable content still persist in Neon ✅
> - TIL **attachments** (uploaded files) will be wiped whenever Render
>   restarts the container (every deploy, every wake-from-sleep, occasional
>   maintenance). Database rows pointing at the file remain; the file body
>   is gone.
> - Workaround: just write text-based TILs for now, or embed external image
>   URLs in markdown. No code change needed.
> - When you're ready to add R2 later: come back here, do Steps 1-6 of this
>   section, paste the env vars into Render, redeploy. Existing
>   attachments will still be missing (they're already gone), but new ones
>   will persist forever.


1. https://dash.cloudflare.com → **R2** in the left sidebar → **Create bucket**.
2. Bucket name: `gokulraam-uploads`. Location: pick closest.
3. After creation, click into the bucket → **Settings** tab.
4. Under **"Public access"**, click **"Allow Access"** for `R2.dev subdomain`. You'll get a public URL like `https://pub-XXXX.r2.dev`. Copy it.
5. Go back to R2 home → **"Manage API tokens"** (top-right) → **"Create API token"**:
   - Token name: `gokulraam-backend`
   - Permissions: **"Object Read & Write"**
   - Specify bucket(s): just `gokulraam-uploads`
   - Click **Create**. You get:
     - **Access Key ID** (visible always)
     - **Secret Access Key** (shown ONCE — copy it now)
     - **S3 API endpoint** (the `https://<account-id>.r2.cloudflarestorage.com` URL)
6. Note your **Account ID** — the dashboard shows it on the right sidebar. You'll need it in Render env.

> Free tier reminder: 10 GB storage, 1M Class A (writes) ops/month, 10M Class B (reads). Way over what a personal site needs.

---

## Step 3 — Render backend

1. https://dashboard.render.com → **New** → **Blueprint**.
2. Connect your GitHub account if you haven't. Select the repo `gokulvibe/gokulraam.dev`.
3. Render reads `render.yaml` and detects the `gokulraam-backend` service. Click **Apply**.
4. The service is created in "deploying" state. While it builds, set the env vars:
   - Click into the service → **Environment** → **Add Environment Variable** for each:

   | Key | Value |
   |-----|-------|
   | `ADMIN_PASSWORD_HASH` | bcrypt hash — run locally: `cd backend && .venv/bin/python -m app.tools.hashpw 'your-real-password'` |
   | `SESSION_SECRET` | run: `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` |
   | `FRONTEND_ORIGIN` | start with `https://gokulraam-dev.pages.dev` — we'll add the custom domain later |
   | `DATABASE_URL` | the Neon pooled connection URL from Step 1 |
   | `R2_ACCOUNT_ID` | your Cloudflare account ID from Step 2 — **omit if skipping R2** |
   | `R2_ACCESS_KEY_ID` | from Step 2 — **omit if skipping R2** |
   | `R2_SECRET_ACCESS_KEY` | from Step 2 — **omit if skipping R2** |
   | `R2_BUCKET` | `gokulraam-uploads` — **omit if skipping R2** |
   | `R2_PUBLIC_URL` | the `https://pub-XXXX.r2.dev` URL from Step 2 — **omit if skipping R2** |

   > If you set zero, some, or all of the `R2_*` vars: only when **all five**
   > are set will the backend switch to R2. Otherwise it stays on local-disk.

5. Click **Save Changes**. Render will redeploy automatically.
6. Once deployment turns green (build takes ~3–5 min on first deploy), note your service URL:
   ```
   https://gokulraam-backend-XXXX.onrender.com
   ```
7. Test the API: `curl https://gokulraam-backend-XXXX.onrender.com/api/health` → should return `{"status":"ok"}`.

> Schema setup is automatic. On first boot, `Base.metadata.create_all()` creates all tables in Neon, the migrator no-ops (clean schema), and seed_* populates default rows.

---

## Step 4 — Cloudflare Pages frontend

1. https://dash.cloudflare.com → **Workers & Pages** → **Create application** → **Pages** → **Connect to Git**.
2. Authorize Cloudflare to access your GitHub. Select `gokulvibe/gokulraam.dev`.
3. Build settings:
   - **Project name**: `gokulraam-dev`
   - **Production branch**: `main`
   - **Framework preset**: **Astro**
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
   - **Root directory**: `frontend`
4. **Environment variables** (click "Add variable" for each):
   | Key | Value |
   |-----|-------|
   | `CF_PAGES` | `1` |
   | `PUBLIC_API_BASE` | your Render service URL from Step 3 (no trailing slash) |
   | `NODE_VERSION` | `20` |
5. Click **Save and Deploy**. First build takes ~3–4 min.
6. When it's done, your site is live at `https://gokulraam-dev.pages.dev`.

---

## Step 5 — Cross-wire CORS + R2

Two settings need to be updated now that the URLs exist:

1. **In Render** → Environment → update `FRONTEND_ORIGIN`:
   ```
   https://gokulraam-dev.pages.dev,https://*.gokulraam-dev.pages.dev
   ```
   (The `*` covers preview deploys for non-main branches.)
   Save → Render auto-redeploys.

2. **In Cloudflare R2** → your bucket → **Settings** → **CORS Policy** → paste: *(skip if you didn't do Step 2)*
   ```json
   [
     {
       "AllowedOrigins": ["https://gokulraam-dev.pages.dev", "http://localhost:4321"],
       "AllowedMethods": ["GET", "HEAD"],
       "AllowedHeaders": ["*"],
       "MaxAgeSeconds": 3600
     }
   ]
   ```
   (Only `GET`/`HEAD` because the frontend never writes directly to R2 — uploads always go through the backend.)

---

## Step 6 — Smoke test

```bash
# Backend
curl https://gokulraam-backend-XXXX.onrender.com/api/health
curl https://gokulraam-backend-XXXX.onrender.com/api/profile

# Frontend renders + can hit backend
open https://gokulraam-dev.pages.dev
```

Walk through these:
- [ ] Homepage loads with dark theme (default)
- [ ] Click `☼` top-right → switches to Daylight theme
- [ ] Press `⌘K` → search modal opens
- [ ] `/til` lists the seeded posts
- [ ] `/work` shows your Saama experience
- [ ] Footer shows `⌘K · search · rss · github · linkedin · email`

If something's broken: open the browser devtools → Network tab → look for `cors` errors (origin mismatch) or `500`s (backend logs in Render dashboard).

---

## Step 7 — Sign in as admin and verify edits persist

1. Go to `https://gokulraam-dev.pages.dev/admin/login`
2. Username: `gokul` · Password: whatever you hashed in step 3
3. AdminBar appears bottom-right → success
4. Visit `/now` → click any item → edit → save
5. Hard-refresh (`⌘⇧R`) → your edit is still there → Neon is wired up correctly

Now upload a TIL attachment to test storage: *(only if you set up R2 in Step 2)*
1. Go to `/til/postgres-explain-buffers` (or any TIL)
2. Drop a small file into the attachments zone
3. Refresh → attachment is still there → R2 is wired up correctly
4. Open the attachment URL in a new tab → should redirect to `pub-XXXX.r2.dev/...`

If you skipped R2: uploads still work, but disappear after a Render restart.
That's expected — see Step 2's note for context.

---

## Step 8 (optional) — Custom domain

When you're ready to buy `gokulraam.dev` (or any other domain):

1. **Buy at Cloudflare Registrar** — https://dash.cloudflare.com → **Domain Registration** → search for `gokulraam.dev` → buy. Renewals are at wholesale cost, no markup.
2. **Point Pages at it**: Cloudflare Pages → your project → **Custom domains** → **Set up a custom domain** → enter `gokulraam.dev`. Cloudflare auto-configures DNS since you bought through them.
3. **Point a subdomain at Render**: Cloudflare DNS → add a CNAME record:
   - Type: `CNAME`
   - Name: `api`
   - Target: `gokulraam-backend-XXXX.onrender.com`
   - Proxy: off (Cloudflare orange-cloud off; let it pass through)
4. **Render**: settings → **Custom Domains** → add `api.gokulraam.dev`. Render handles SSL automatically.
5. **Update env vars**:
   - In **Render** → `FRONTEND_ORIGIN` = `https://gokulraam.dev,https://gokulraam-dev.pages.dev`
   - In **Cloudflare Pages** → `PUBLIC_API_BASE` = `https://api.gokulraam.dev`
   - Trigger a redeploy on both.
6. **R2 CORS** (Step 5 #2) → add `https://gokulraam.dev` to `AllowedOrigins`.

DNS takes 1-5 min to propagate. Then `gokulraam.dev` serves your frontend and `api.gokulraam.dev` serves your backend.

---

## Day-2 operations

### Updating the site
Just `git push origin main`. Both Render and Cloudflare Pages have GitHub integration and auto-deploy. Render takes ~3-5 min, Pages ~2 min.

### Inspecting logs
- **Backend** — Render dashboard → your service → **Logs** tab (live tail)
- **Frontend** — Cloudflare dashboard → Pages → **Deployments** → click the latest → **View build log**

### Local dev still works the same
Nothing changed for local development. `make dev` still runs against SQLite + local-disk uploads. The Postgres/R2 envs are only set in production.

### Troubleshooting

**Backend stuck on old code (auto-deploy not triggering)**

Symptoms: frontend updates fine on every push (you see new pages), but
`curl https://gokulraam-backend.onrender.com/openapi.json` shows fewer routes
than your local backend, or new endpoints return 404 in prod. The `/admin/stats`
dashboard breaks because the new stats endpoints aren't there.

Diagnose & fix:
1. Render dashboard → `gokulraam-backend` → **Events** tab
2. Look for the most recent build attempt:
   - **No recent attempts** → auto-deploy is paused. Settings → Auto-Deploy → set to Yes → Manual Deploy → "Deploy latest commit".
   - **Failed builds** → click the failed one → read the log. Most common cause is a new dependency that didn't build on Render's image. Fix the requirement and push again.
   - **Queued/in progress** → free tier is slow on cold pickup. Wait 10 min then manual deploy if still nothing.
3. Push an empty commit to nudge the webhook if needed:
   ```sh
   git commit --allow-empty -m "chore: trigger render redeploy"
   git push
   ```

**Uploaded photo disappeared after redeploy**

Expected on the free tier — Render's filesystem is ephemeral. The Photo DB
row still exists; only the file on disk is gone. Options:
- For permanence: paste external URLs (GitHub raw, Imgur direct, picsum) via the "paste url" tab in `/photos` instead of uploading
- For proper fix: add a card to Cloudflare → set `R2_*` env vars on Render → storage abstraction switches automatically, no code change

**CORS errors after a deploy**

Check `FRONTEND_ORIGIN` on Render. Should be a comma-separated list including:
- `https://gokulraam-dev.pages.dev`
- `https://*.gokulraam-dev.pages.dev` (preview branches)
- `https://gokulraam.dev` (when the custom domain lands)

**Admin login works locally but fails on prod**

Verify `COOKIE_SECURE=true` is set on Render. Without it, the cookie is `SameSite=Lax`
without `Secure`, which the browser refuses to send cross-origin from Pages → Render.

### Backing up your DB
Neon has built-in PITR (point-in-time recovery) on the free tier. For belt-and-braces:
```bash
pg_dump $NEON_URL > backups/dump-$(date +%Y%m%d).sql
```
Tuck the dump anywhere safe (Drive, R2, etc.).

---

## Migrating to a paid host later

Because this stack is host-agnostic by design, the move from Render → Hetzner / DigitalOcean / Oracle / wherever takes ~1-2 hours:

| What | Migration step | Time |
|---|---|---|
| Code | `git push` to new host, or `git clone` on a VPS | 5 min |
| Database | `pg_dump $OLD_NEON > out.sql && psql $NEW_DB < out.sql` (or keep Neon — it works from any host) | 10 min |
| File uploads | Already on R2 — works from any host without migration | 0 min |
| Env vars | Copy from Render dashboard to new host's env | 5 min |
| Build/run config | Render → systemd / docker-compose / new PaaS config | 30-60 min |
| DNS | Update Cloudflare DNS A/CNAME records | 5 min + ~5 min propagation |
| **Total** | | **~1-2 hours** |

The only lock-in is the build/run config — and that's a single file per host.

---

## Reference: full env-var table

### Render (backend service env vars)
```
ADMIN_USERNAME=gokul
ADMIN_PASSWORD_HASH=$2b$12$...           ← from app.tools.hashpw
SESSION_SECRET=...                       ← secrets.token_urlsafe(48)
FRONTEND_ORIGIN=https://gokulraam-dev.pages.dev,https://gokulraam.dev
DATABASE_URL=postgresql://...?sslmode=require   ← from Neon
R2_ACCOUNT_ID=...                        ← Cloudflare account ID
R2_ACCESS_KEY_ID=...                     ← R2 API token
R2_SECRET_ACCESS_KEY=...                 ← R2 API token
R2_BUCKET=gokulraam-uploads
R2_PUBLIC_URL=https://pub-XXXX.r2.dev    ← public R2 URL
```

### Cloudflare Pages (frontend build env vars)
```
CF_PAGES=1                               ← triggers cloudflare adapter at build
PUBLIC_API_BASE=https://gokulraam-backend-XXXX.onrender.com
NODE_VERSION=20
```
