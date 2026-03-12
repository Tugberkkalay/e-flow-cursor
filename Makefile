.PHONY: up down dev-api dev-web migrate seed install

up:
	docker compose up -d

down:
	docker compose down

dev-api:
	cd apps/api && uvicorn app.main:app --reload --port 8000

dev-web:
	cd apps/web && npm run dev

install:
	cd apps/api && pip install -r requirements.txt
	cd apps/web && npm install

migrate:
	cd apps/api && alembic upgrade head

seed:
	cd apps/api && python -m app.seed

test-api:
	cd apps/api && pytest tests/ -v

test-web:
	cd apps/web && npx playwright test

lint:
	cd apps/web && npm run lint
	cd apps/api && ruff check app/
