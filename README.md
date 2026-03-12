# e-Flow Enterprise

Enterprise BPM & Workflow Automation Platform

## Architecture

```
/workspace
├── apps/
│   ├── api/          # FastAPI backend (Python 3.12)
│   │   ├── app/
│   │   │   ├── engine/       # BPM runtime engine + expression engine
│   │   │   ├── models/       # SQLAlchemy models
│   │   │   ├── routers/      # API endpoints
│   │   │   ├── schemas/      # Pydantic schemas
│   │   │   ├── services/     # Auth, etc.
│   │   │   ├── main.py       # FastAPI app
│   │   │   └── seed.py       # Seed data
│   │   └── tests/            # Pytest tests
│   └── web/          # Next.js frontend (TypeScript)
│       └── src/
│           ├── app/          # Pages (App Router)
│           ├── components/   # UI components
│           ├── lib/          # Utilities, node registry, templates
│           ├── store/        # Zustand state
│           └── types/        # TypeScript types
```

## Quick Start

### Backend (API)

```bash
cd apps/api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.seed          # Seed database
uvicorn app.main:app --reload --port 8000
```

### Frontend (Web)

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000 — Login: `admin@eflow.io` / `admin123`

## Features

- **Flow Designer**: Drag-and-drop canvas with 40+ node types, smart curved edges, mini-map
- **Form Builder**: Dynamic fields, conditional rules, calculations, line-items
- **BPM Engine**: Lazy step-by-step execution, {{ expression }} support, gateway semantics
- **Approval System**: Single/multi/limit-matrix approvals, delegation, vacation fallback
- **Process Management**: Start, track, reassign, retry, skip, cancel instances
- **Inbox**: Pending approvals and tasks with approve/reject/revision actions
- **User Management**: RBAC (admin/approver/viewer), delegation, approval limit matrix
- **Audit Log**: Immutable event stream, filterable, CSV export
- **4 Domain Templates**: Purchase Request, P2P, Contract, Invoice/Payment

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/auth/login | Login |
| GET | /api/auth/me | Current user |
| GET/POST | /api/flows | List/Create flows |
| PUT | /api/flows/{id} | Update flow |
| POST | /api/flows/{id}/publish | Publish flow |
| GET | /api/flows/{id}/versions | Flow versions |
| GET/POST | /api/forms | List/Create forms |
| PUT | /api/forms/{id} | Update form |
| POST | /api/forms/{id}/publish | Publish form |
| POST | /api/instances/start | Start instance |
| GET | /api/instances | List instances |
| GET | /api/instances/{id} | Instance detail |
| POST | /api/instances/{id}/actions | Instance actions |
| GET | /api/instances/{id}/timeline | Timeline events |
| GET | /api/inbox | Pending tasks/approvals |
| POST | /api/tasks/{id}/complete | Complete task |
| POST | /api/approvals/{id}/decide | Decide approval |
| GET/POST | /api/users | CRUD users |
| GET/POST | /api/delegations | CRUD delegations |
| GET/POST | /api/approval-limits | CRUD limits |
| GET | /api/audit | Audit events |
| POST | /api/expressions/preview | Expression preview |
| GET | /api/context/schema | Context autocomplete |

## Seed Data

- 4 users: admin, procurement approver, finance approver, legal
- 4 flow templates (published)
- 1 form (PR form with 12 fields)
- 3 approval limit tiers (0-50K, 50K-250K, 250K+)
- 1 delegation record

## Tests

```bash
cd apps/api && source venv/bin/activate
python -m pytest tests/ -v
```
