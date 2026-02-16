# CNFund Backend API (FastAPI)

Backend API cho CNFund, dùng nghiệp vụ từ `core/services_enhanced.py` và lưu dữ liệu nghiệp vụ trên PostgreSQL.

## Prerequisites

- Python 3.11+
- PostgreSQL

## Install

```powershell
.\.venv\Scripts\python -m pip install -r backend_api/requirements.txt
```

## Configure

Copy env mẫu:

```powershell
Copy-Item backend_api/.env.example .env
```

Các biến chính:

- `API_DATABASE_URL` (bắt buộc, PostgreSQL)
- `API_JWT_SECRET_KEY`
- `API_ADMIN_USERNAME`
- `API_ADMIN_PASSWORD`
- `API_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`
- `API_ALLOWED_ORIGIN_REGEX=https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?$`
- `API_FEATURE_TABLE_VIEW=true`
- `API_FEATURE_BACKUP_RESTORE=true`
- `API_FEATURE_FEE_SAFETY=true`
- `API_FEATURE_TRANSACTIONS_LOAD_MORE=true`
- `API_AUTO_BACKUP_ON_NEW_TRANSACTION=true`
- `GOOGLE_DRIVE_FOLDER_ID=<drive-folder-id-or-url>`
- `GOOGLE_OAUTH_TOKEN_BASE64=<base64-token-from-token.pickle>`

Bootstrap dữ liệu CSV một lần khi DB rỗng:

- `API_POSTGRES_BOOTSTRAP_FROM_CSV=true|false`
- `API_POSTGRES_SEED_DIR=<path-optional>`

## Run

```powershell
.\.venv\Scripts\python -m uvicorn backend_api.app.main:app --reload --host 127.0.0.1 --port 8001
```

API docs:
- Swagger: `http://127.0.0.1:8001/docs`
- OpenAPI: `http://127.0.0.1:8001/openapi.json`

## One-command full stack

```powershell
npm run dev
```

## Safety controls

- Mutating operations được serialize bằng runtime lock.
- `POST /fees/apply` yêu cầu:
  - `confirm_token` từ `POST /fees/preview`
  - `acknowledge_risk=true`
  - `acknowledge_backup=true`
- `POST /backups/restore` yêu cầu:
  - `confirm_phrase="RESTORE"`
  - `create_safety_backup` (khuyến nghị: `true`)

## Quick checks

```powershell
.\.venv\Scripts\python -m compileall backend_api/app
```

## Deployment

Xem `docs/DEPLOYMENT_LOW_COST_STABLE.md`.
