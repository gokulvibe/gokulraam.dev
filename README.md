# gokulraam-site

Personal site + dev portfolio for Gokul Raam. Editorial dark TCG-folio
aesthetic ("Nocturnal Folio") with an alternate light theme. Every page
is admin-editable in place.

**Live**: [gokulraam-dev.pages.dev](https://gokulraam-dev.pages.dev)
**Repo**: [github.com/gokulvibe/gokulraam.dev](https://github.com/gokulvibe/gokulraam.dev)

> **Docs**
> - [CLAUDE.md](./CLAUDE.md) — quick context for Claude Code sessions (project layout, conventions, known issues)
> - [SPEC.md](./SPEC.md) — product spec + design system + editing convention
> - [ROADMAP.md](./ROADMAP.md) — what's shipped, what's next, full changelog
> - [DEPLOY.md](./DEPLOY.md) — production deployment walkthrough

## Stack

| Layer | Local | Production |
|---|---|---|
| Frontend | Astro 4 (hybrid) + Tailwind + MDX + React islands @ :4321 | Cloudflare Pages |
| Backend | FastAPI + uvicorn @ :8000 | Render free |
| DB | SQLite | Neon Postgres (pooled) |
| Files | Local disk | Local disk (ephemeral) — R2 ready |

## Run

```sh
make install   # one-time: installs frontend + backend deps
make dev       # starts both servers
```

Then open:
- http://localhost:4321 — public site
- http://localhost:8000/docs — API docs (Swagger)

Admin sign-in lives at `/admin/login`. Hash your password locally:
```sh
cd backend && .venv/bin/python -m app.tools.hashpw 'your-password'
```

## Layout

```
gokulraam-site/
├── frontend/        Astro app — public pages + admin chrome inline
├── backend/         FastAPI app — admin, content APIs, badminton scraper, OG image gen
├── Makefile         `make dev` runs both
├── render.yaml      Render blueprint
└── frontend/wrangler.toml   Cloudflare Workers config
```

See [CLAUDE.md](./CLAUDE.md) for a deeper map and conventions.

## Current state

The site is live in production. **Backend auto-deploy on Render is currently
stuck** — frontend has updated through many recent commits but the backend
hasn't picked them up, so `/admin/stats`, `/photos` add/upload/delete, and
`/logbook` write endpoints don't work in prod yet. See
[ROADMAP.md → Known issues](./ROADMAP.md#current-state-snapshot--2026-06-01) for the fix.

## License

Personal project. Code is unlicensed for now — please don't copy wholesale.
If you'd like to use any piece, open an issue.
