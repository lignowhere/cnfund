# CNFund Backend API (FastAPI)

FastAPI backend for the CNFund strangler migration, reusing business logic from `core/services_enhanced.py`.

## Prerequisites

- Python 3.11+
- Existing CNFund project files (`core/`, `integrations/`, `data/`)

## Install

```powershell
.\.venv\Scripts\python -m pip install -r backend_api/requirements.txt
```

## Configure

Copy env file:

```powershell
Copy-Item backend_api/.env.example .env
```

Main env vars:

- `API_DATABASE_URL` (PostgreSQL for auth + business data)
- `API_CNFUND_DATA_SOURCE=postgres` (recommended), or `csv|drive` for legacy mode
- `API_POSTGRES_BOOTSTRAP_FROM_CSV=true|false` (optional one-time import when DB is empty)
- `API_POSTGRES_SEED_DIR=<path>` (optional directory for 4 CSV seed files)
- `API_JWT_SECRET_KEY`
- `API_ADMIN_USERNAME`
- `API_ADMIN_PASSWORD`
- `API_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`
- `API_ALLOWED_ORIGIN_REGEX=https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?$` (cho phép dev port linh hoạt như `3001`, `3002`)
- `API_FEATURE_TABLE_VIEW=true`
- `API_FEATURE_BACKUP_RESTORE=true`
- `API_FEATURE_FEE_SAFETY=true`
- `API_FEATURE_TRANSACTIONS_LOAD_MORE=true`

## Run

```powershell
cd backend_api
..\.venv\Scripts\python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Note: if the above path spacing is inconvenient, run from repo root:

```powershell
.\.venv\Scripts\python -m uvicorn backend_api.app.main:app --reload --host 127.0.0.1 --port 8001
```

API docs:

- Swagger: `http://127.0.0.1:8001/docs`
- OpenAPI: `http://127.0.0.1:8001/openapi.json`

### One-command run for full stack

From repo root:

```powershell
npm run dev
```

## Core modules

- Auth JWT + RBAC (`viewer`, `admin`, `fund_manager`)
- Investors, transactions, NAV, fees, reports, backups
- Feature flags: `GET /api/v1/system/feature-flags`

## Safety controls

- Mutating operations are serialized with runtime lock.
- `POST /fees/apply` requires:
  - `confirm_token` from `POST /fees/preview`
  - `acknowledge_risk=true`
  - `acknowledge_backup=true`
- `POST /backups/restore` requires:
  - `confirm_phrase="RESTORE"`
  - `create_safety_backup` (recommended: `true`)

## Quick checks

```powershell
.\.venv\Scripts\python -m compileall backend_api/app
```

## Production deployment recommendation

See `docs/DEPLOYMENT_LOW_COST_STABLE.md` for the lowest-cost stable deployment plan with backup policy.
