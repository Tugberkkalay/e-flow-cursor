# e-Flow Enterprise

**Production-grade Enterprise BPM / Workflow Automation Platform**

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 (App Router) + TypeScript + TailwindCSS |
| Canvas | React Flow (custom nodes + smart curved edges) |
| State | Zustand + TanStack Query |
| Backend | FastAPI + Pydantic v2 |
| Database | PostgreSQL (SQLAlchemy async + Alembic) |
| Auth | JWT + RBAC |
| Tests | Pytest (66 tests) |

## Quick Start (Local Dev)

### Backend
```bash
cd apps/api
pip install -r requirements.txt
# Start PostgreSQL and create database
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd apps/web
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

### Docker Compose
```bash
docker compose up -d
```

## Demo Credentials

| User | Email | Password | Role |
|------|-------|----------|------|
| Admin | admin@eflow.com | admin123 | admin |
| Satın Alma | procurement@eflow.com | proc123 | procurement |
| Finans | finance@eflow.com | fin123 | finance |
| Hukuk | legal@eflow.com | leg123 | legal |

## Features

### Flow Designer (Canvas)
- Knowledge-graph feel with smart curved/smoothstep edges
- Drag-and-drop node palette (9 categories, 35+ node types)
- Properties panel with per-node config editors
- Auto-save + keyboard shortcuts (Ctrl+S)
- Publish/Draft versioning

### Dynamic Form Builder
- 10 field types: text, textarea, number, money, date, dropdown, multi-select, boolean, file-upload, line-items
- Conditional visibility/required rules
- Calculation fields (KDV, totals, FX)

### BPM Runtime Engine (Lazy Execution)
- **Key principle**: Next node computed at runtime, not upfront
- Expression engine: `{{ form.total_amount * 1.20 }}` with safe AST eval
- Gateway semantics: IF, Switch, Parallel Split/Join
- Error handling: retry policy, idempotency, stop & error
- Approval routing via Limit Matrix
- Subprocess/SubprocessCall skeleton with input/output mapping

### Enterprise Features
- RBAC: admin, approver, viewer, procurement, finance, legal
- Delegation (vekalet) with date range + role scope
- Approval Limit Matrix: 0–50K → Manager, 50K–250K → Director, 250K+ → CFO
- Immutable Audit Log (AuditEvent table, append-only)
- Process Instance Detail: Timeline, Tasks, Approvals, Form Snapshot, Documents

### Domain Templates (4 seeded flows)
1. **Satın Alma Talebi (PR)** - Form → Calculate → IF(≥50K) → Doc Upload → Policy Check → End
2. **Satın Alma Süreci (P2P)** - Check Offers → Vendor Selection → Limit Matrix Approval → PO → ERP(Mock)
3. **Sözleşme Süreci** - Doc Upload → AI Extract(Stub) → Legal Review → Revision Loop → Finance Approval → E-Sign(Stub) → Archive
4. **Sipariş/Fatura/Ödeme** - Delivery → Invoice Upload → Extract → 3-Way Match → Switch(matched/mismatch) → Payment/Dispute

## API Documentation

Available at `http://localhost:8000/docs` (Swagger UI)

## Testing

```bash
# Backend tests (66 passing)
cd apps/api && pytest tests/ -v

# Coverage breakdown:
# - test_expression_engine.py: 49 tests
#   Expression resolution, arithmetic, conditions, resolve_all, context schema
# - test_bpm_engine.py: 43 tests
#   Graph traversal, gateway routing, script logic, domain template structure
# - test_api.py: 17 tests
#   Auth, CRUD, instance lifecycle, expression preview
```

## Architecture

```
apps/
├── api/               # FastAPI backend
│   ├── app/
│   │   ├── models/    # SQLAlchemy models
│   │   ├── routers/   # FastAPI routers
│   │   ├── engine/    # BPM Engine + Expression Engine
│   │   └── seed.py    # Demo data seeder
│   ├── alembic/       # Database migrations
│   └── tests/         # Pytest test suite
└── web/               # Next.js frontend
    └── src/
        ├── app/       # Next.js App Router pages
        ├── components/# UI components
        │   ├── flow/  # Flow Designer components
        │   ├── layout/# Sidebar + Header
        │   └── instances/ # Process instance components
        ├── lib/       # API client, utils, node registry
        └── store/     # Zustand stores
```
