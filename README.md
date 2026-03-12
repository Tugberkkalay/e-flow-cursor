# e-Flow Enterprise

Enterprise BPM / Workflow Automation monorepo with:

- `apps/web` — Next.js 16 + TypeScript + Tailwind + React Flow
- `apps/api` — FastAPI + SQLAlchemy + Alembic skeleton + lazy BPM runtime

## Features

- Apple-like enterprise UI shell
- Flow Designer with custom smart routed/curved edges
- Dynamic Form Builder view with seeded schemas
- Lazy BPM runtime engine with runtime next-node resolution
- `{{ }}` expression preview endpoint
- RBAC, delegation, approval limit matrix, immutable audit trail
- 4 seeded domain templates:
  - Purchase Request (PR)
  - Purchase to Pay (P2P)
  - Contract Process
  - Invoice Match / Payment

## Demo credentials

- Email: `admin@eflow.local`
- Password: `admin123`

## Run locally

### API

```bash
cd apps/api
pip3 install -e '.[dev]'
python3 -m uvicorn app.main:app --reload --port 8000
```

### Web

```bash
cd apps/web
npm install
npm run dev
```

## Test

```bash
cd apps/api && python3 -m pytest
cd /workspace && npx playwright test
```
