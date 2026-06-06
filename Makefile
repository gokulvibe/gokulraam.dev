.PHONY: install dev frontend backend migrate migrate-new clean

install:
	cd frontend && npm install
	cd backend && python3.12 -m venv .venv && .venv/bin/pip install -U pip && .venv/bin/pip install -r requirements.txt

# Run DB migrations (alembic upgrade head). Safe to re-run.
# Bootstrap-aware: handles fresh DB / legacy populated DB / normal upgrades.
migrate:
	cd backend && .venv/bin/python -m app.migrate

# Scaffold a new migration. Pass NAME=description on the CLI.
#   make migrate-new NAME="add foo to bar"
# Use --autogenerate when adding/renaming model fields; for data-only
# changes (UPDATE/INSERT/DELETE) just edit the generated file by hand.
migrate-new:
	cd backend && .venv/bin/alembic revision --autogenerate -m "$(NAME)"

dev: migrate
	@echo "Starting frontend (4321) and backend (8000)..."
	@trap 'kill 0' INT; \
		(cd frontend && npm run dev) & \
		(cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000) & \
		wait

frontend:
	cd frontend && npm run dev

backend: migrate
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

clean:
	rm -rf frontend/node_modules frontend/dist frontend/.astro
	rm -rf backend/.venv backend/data/*.db
