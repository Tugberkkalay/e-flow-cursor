# AGENTS.md

## Cursor Cloud specific instructions

### Overview

e-Flow Enterprise is a monorepo with two services:

| Service | Directory | Port | Stack |
|---------|-----------|------|-------|
| API | `apps/api` | 8000 | Python 3.12, FastAPI, SQLAlchemy, SQLite |
| Web | `apps/web` | 3000 | Next.js 16, React 19, Tailwind v4, React Flow |

No external services (databases, caches, queues) are required — SQLite is embedded.

### Running services

- **API**: `cd apps/api && python3 -m uvicorn app.main:app --reload --port 8000`
- **Web**: `cd apps/web && npm run dev`

The API auto-seeds demo data (users, flow templates) on first startup. The web frontend auto-authenticates with demo credentials (`admin@eflow.local` / `admin123`). The Next.js server-side API client connects directly to `http://127.0.0.1:8000`.

### Lint / Test / Build

See `package.json` root scripts. Key commands:

- **API tests**: `cd apps/api && python3 -m pytest tests/ -v`
- **Web lint**: `cd apps/web && npx eslint .`
- **Web build**: `cd apps/web && npm run build`

### Gotchas

- The SQLite database file (`apps/api/e_flow_enterprise.db`) is created on first API startup and is gitignored. Deleting it resets all data; the seeder re-populates on next start.
- The API uses `pip install -e '.[dev]'` (editable install from `pyproject.toml`), not a `requirements.txt`.
- Starting a process instance uses `POST /instances/start` with `{flow_version_id, initial_inputs}`. Get `flow_version_id` from `GET /flows/{flow_id}/versions`.
