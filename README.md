# e-Flow Enterprise (Monorepo)

Enterprise BPM / Workflow Automation MVP (production-grade mimari yaklaşımıyla).

## Stack

- **Frontend:** Next.js (App Router) + TypeScript + Tailwind + shadcn-style UI + React Flow + Zustand
- **Backend:** FastAPI + Pydantic + SQLAlchemy + Alembic
- **DB:** PostgreSQL uyumlu şema (varsayılan local SQLite ile hızlı başlatma)
- **Tests:** Pytest + Playwright smoke

## Monorepo Yapısı

```text
/apps
  /api   # FastAPI + BPM runtime engine
  /web   # Next.js UI (Designer, Form Builder, Instances, Inbox, Users, Audit)
```

## Çalıştırma

### 1) API

```bash
cd apps/api
python3 -m pip install -e ".[dev]"
python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

> `DATABASE_URL` verilmezse `sqlite:///./eflow.db` kullanılır. PostgreSQL için `.env` içinde `database_url=postgresql+psycopg://...` tanımlayabilirsiniz.

### 2) Web

```bash
cd apps/web
npm install
npm run dev
```

`NEXT_PUBLIC_API_URL` default olarak `http://localhost:8000`.

## Seed İçeriği

- 4 kullanıcı:
  - `admin@eflow.local / admin123`
  - `procurement@eflow.local / demo123`
  - `finance@eflow.local / demo123`
  - `legal@eflow.local / demo123`
- Approval limit matrix:
  - 0-50k → manager
  - 50k-250k → director
  - 250k+ → cfo
- 4 domain template:
  - Satın Alma Talebi (PR)
  - Satın Alma Süreci (P2P)
  - Sözleşme Süreci
  - Sipariş/Fatura/Ödeme

## Uygulanan Çekirdek Özellikler

- Flow Designer:
  - Knowledge-graph hissi veren canvas
  - Smart curved/routed custom edge (`SmartCurvedRoutedEdge`)
  - Node palette + kategoriler + arama
  - Properties panel + config JSON
  - Auto arrange (dagre), minimap, zoom controls
- Dynamic Form Builder:
  - Alan tipleri + rule/calculation alanları
  - Stable key yaklaşımı (`snake_case`)
- BPM Runtime (lazy execution):
  - Node tamamlandıkça next node runtime’da hesaplanır
  - Human task / approval wait-state
  - Gateway IF/SWITCH route
  - End export mapping
  - Retry / skip / cancel admin aksiyonları
- Expression engine:
  - `{{ }}` çözümleme
  - Safe AST tabanlı arithmetic/boolean evaluation
  - `/context/schema` ve `/expressions/preview`
- Enterprise:
  - JWT auth + RBAC guard
  - Delegation modeli
  - Approval limit matrix route
  - Immutable audit event stream + CSV export
- Reuse:
  - SubprocessCall / legacy adapter skeleton

## Testler

### Backend

```bash
cd apps/api
python3 -m pytest -q
```

### Frontend

```bash
cd apps/web
npm run lint
npm run build
npm run test:e2e
```
