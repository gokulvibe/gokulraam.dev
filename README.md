# gokulraam-site

Personal site + dev portfolio for Gokul Raam.

> **Docs**: [SPEC.md](./SPEC.md) — what this site is · [ROADMAP.md](./ROADMAP.md) — what's done, what's next

## Stack

- **Frontend** — Astro 4 + Tailwind + MDX (static, runs at `localhost:4321`)
- **Backend** — FastAPI + SQLite (Python 3.12, runs at `localhost:8000`)
- **Aesthetic** — "Nocturnal Collector's Folio" (dark TCG-folio)

## Layout

```
gokulraam-site/
├── frontend/        Astro app (public site)
├── backend/         FastAPI app (admin + TIL API + badminton fetcher)
└── Makefile         `make dev` runs both
```

## Run

```sh
make install   # one-time: installs frontend + backend deps
make dev       # starts both servers
```

Then open:
- http://localhost:4321 — public site
- http://localhost:8000/docs — API docs (Swagger)

## Future-proofing

- **Three.js / WebGL** — drop a `<script>` or React-three-fiber island in any Astro page.
- **State management** — Nano Stores for shared state; Zustand inside React islands for complex flows.
- **Going SPA later** — React components + Tailwind port cleanly to Next.js. No lock-in.
