.PHONY: install dev frontend backend clean

install:
	cd frontend && npm install
	cd backend && python3.12 -m venv .venv && .venv/bin/pip install -U pip && .venv/bin/pip install -r requirements.txt

dev:
	@echo "Starting frontend (4321) and backend (8000)..."
	@trap 'kill 0' INT; \
		(cd frontend && npm run dev) & \
		(cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000) & \
		wait

frontend:
	cd frontend && npm run dev

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

clean:
	rm -rf frontend/node_modules frontend/dist frontend/.astro
	rm -rf backend/.venv backend/data/*.db
