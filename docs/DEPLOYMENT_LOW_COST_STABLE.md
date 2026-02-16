# CNFund Deploy Plan (Cheapest Stable)

## 1) Target architecture (recommended)

- Frontend: Vercel Hobby (Next.js)  
- Backend API: Railway Hobby (FastAPI service)  
- Auth/Audit DB: Railway PostgreSQL (inside same Railway project)  
- Business data store: Railway Volume mounted for `data/` + `exports/`  
- Backup layer:
  - Railway Postgres backups (native, scheduled)
  - Railway Volume backups (native, scheduled)
  - App-level manual backup (`/api/v1/backups/manual`) before risky operations

This is the lowest-cost setup that is still stable for production-like usage.

## 2) Why this plan

- Vercel Hobby is valid for personal/non-commercial use.
- Streamlit Community Cloud hibernates inactive apps and has tighter resource constraints; not ideal for always-available API + modern FE stack.
- Railway Free is too constrained for reliable multi-service operation; Railway Hobby is low cost and materially more stable.

## 3) Cost expectation

- Vercel Hobby: $0/month (personal/non-commercial scope).
- Railway Hobby: $5 minimum usage/month, includes $5 usage credits.
- If monthly usage <= included credit, practical baseline is around $5/month for backend side.
- Backup storage consumes additional Railway storage usage, usually small at this scale.

## 4) Data safety policy (must-have)

- RPO target: <= 24h
- RTO target: <= 60 minutes
- Retention:
  - Daily backups: 7 days
  - Weekly backups: 4 weeks
  - Monthly backups: 3 months
- Monthly restore drill: restore to staging and verify key reports.

## 5) Deploy steps (exact for this repo)

### Step A: Backend + DB on Railway

1. Create Railway project.
2. Add PostgreSQL service.
3. Deploy backend from this repo (service root at repo root).
4. Create 1 Volume for backend service:
   - mount path: `/app/storage`
   - this is required because Railway supports one volume per service.
   - we will map runtime folders `data` and `exports` into this volume via symlink in start command.
5. Set backend start command:

```bash
mkdir -p /app/storage/data /app/storage/exports && ln -sfn /app/storage/data /app/data && ln -sfn /app/storage/exports /app/exports && python -m uvicorn backend_api.app.main:app --host 0.0.0.0 --port $PORT
```

6. Set backend env vars:

```env
API_ENVIRONMENT=production
API_DATABASE_URL=${{Postgres.DATABASE_URL}}
API_CNFUND_DATA_SOURCE=csv
API_JWT_SECRET_KEY=<very-strong-random-secret>
API_ADMIN_USERNAME=<your-admin-user>
API_ADMIN_PASSWORD=<strong-password>
API_ALLOWED_ORIGINS=https://<your-vercel-domain>,https://<your-custom-domain>
API_ALLOWED_ORIGIN_REGEX=
API_FEATURE_TABLE_VIEW=true
API_FEATURE_BACKUP_RESTORE=true
API_FEATURE_FEE_SAFETY=true
API_FEATURE_TRANSACTIONS_LOAD_MORE=true
```

7. Initial data migration:
   - Upload your real CSV files (`investors.csv`, `tranches.csv`, `transactions.csv`, `fee_records.csv`) into mounted `/app/storage/data` (or `/app/data` via symlink).
   - Confirm API health and reports.

### Step B: Frontend on Vercel

1. Import `frontend_app` as a Vercel project.
2. Framework preset: Next.js.
3. Root directory: `frontend_app`.
4. Add env var:

```env
NEXT_PUBLIC_API_BASE_URL=https://<your-railway-backend-domain>/api/v1
```

5. Deploy and verify login + core flows.

## 6) Backup configuration (Railway)

### PostgreSQL backups

- Open PostgreSQL service -> Backups.
- Enable:
  - Daily
  - Weekly
  - Monthly

### Volume backups

- Open backend service volume -> Backups.
- Enable:
  - Daily
  - Weekly
  - Monthly

### App-level safety backup

- Keep using existing backup endpoint:
  - `POST /api/v1/backups/manual`
  - `POST /api/v1/backups/restore` (requires `RESTORE` phrase)
- Requirement: always trigger manual backup before destructive changes (bulk edits, restore, major imports).

## 7) Monitoring & operation checklist

- Daily:
  - `GET /health` returns `status=ok`
  - latest backup exists in volume backup list
- Weekly:
  - verify one manual backup can be created from UI/API
- Monthly:
  - full restore drill in staging from backup
  - verify 3 critical outputs:
    - dashboard totals
    - investor report sample
    - transaction history consistency

## 8) Security baseline

- Rotate `API_JWT_SECRET_KEY` every 90 days.
- Use long random admin password (>=16 chars).
- Restrict CORS only to production frontend domain(s).
- Do not commit credentials/tokens/files containing secrets.

## 9) Notes about Google Drive source

- Current backend supports `API_CNFUND_DATA_SOURCE=drive`, but the existing Drive handler was originally built around Streamlit runtime behavior.
- For cheapest + stable production now, prefer `csv` + Railway Volumes + Railway Backups.
- If you still want Drive as primary store for API deployment, schedule a dedicated refactor to remove Streamlit runtime dependency from Drive adapter first.

## 10) Click-by-click checklist (Railway + Vercel)

Use this checklist exactly in order.

### A. Prepare repository and credentials

1. Ensure branch is clean and pushed to GitHub.
2. Confirm these files exist locally:
   - `backend_api/`
   - `frontend_app/`
   - `data/investors.csv`
   - `data/tranches.csv`
   - `data/transactions.csv`
   - `data/fee_records.csv`
3. Prepare production secrets:
   - strong `API_JWT_SECRET_KEY` (random, long)
   - strong `API_ADMIN_PASSWORD`

### B. Railway setup (backend + database + persistent data)

0. Enable Config as Code:
   - service -> `Settings` -> `Config as Code`.
   - enable and select file: `/railway.toml`.
   - commit this file in repo so every deploy uses the same config.

1. Open Railway dashboard -> `New Project`.
2. Click `Deploy from GitHub repo` and select this repository.
3. In the created service:
   - `Settings` -> set `Root Directory` to repository root (leave empty/default if root).
   - do not manually override Start Command if Config as Code is enabled (it is defined in `railway.toml`).

4. Add PostgreSQL:
   - Project -> `New` -> `Database` -> `Add PostgreSQL`.
5. Connect backend env vars:
   - Backend service -> `Variables` -> add:

```env
API_ENVIRONMENT=production
API_DATABASE_URL=${{Postgres.DATABASE_URL}}
API_CNFUND_DATA_SOURCE=csv
API_JWT_SECRET_KEY=<very-strong-random-secret>
API_ADMIN_USERNAME=<your-admin-user>
API_ADMIN_PASSWORD=<strong-password>
API_ALLOWED_ORIGINS=https://<your-vercel-domain>,https://<your-custom-domain>
API_ALLOWED_ORIGIN_REGEX=
API_FEATURE_TABLE_VIEW=true
API_FEATURE_BACKUP_RESTORE=true
API_FEATURE_FEE_SAFETY=true
API_FEATURE_TRANSACTIONS_LOAD_MORE=true
```

6. Attach persistent volume:
   - Backend service -> `Volumes` -> `New Volume`.
   - Mount path: `/app/storage`.
7. Redeploy backend service.
8. Verify backend:
   - open backend public URL + `/health`, expect `status: ok`.
   - open backend public URL + `/docs`, Swagger should load.

### C. Upload real data to persistent volume

Option 1 (preferred): deploy once with seed data committed in repo and then use app backups/restore.

Option 2 (direct file upload):
1. Open Railway volume file browser.
2. Create folders:
   - `/app/storage/data`
   - `/app/storage/exports`
3. Upload 4 CSV files into `/app/storage/data`:
   - `investors.csv`
   - `tranches.csv`
   - `transactions.csv`
   - `fee_records.csv`
4. Redeploy backend.
5. Validate in API:
   - login works
   - dashboard has real values
   - investor reports are non-empty.

### D. Vercel setup (frontend)

1. Open Vercel -> `Add New...` -> `Project`.
2. Import the same GitHub repository.
3. Configure:
   - Framework: `Next.js`
   - Root Directory: `frontend_app`
4. Add environment variable:

```env
NEXT_PUBLIC_API_BASE_URL=https://<your-railway-backend-domain>/api/v1
```

5. Deploy.
6. Open Vercel app URL:
   - test `/login`
   - login with admin account
   - verify dashboard, investors, transactions, fees, backups.

### E. Backup hardening (critical)

1. Railway PostgreSQL -> `Backups`:
   - enable Daily, Weekly, Monthly.
2. Railway Volume -> `Backups`:
   - enable Daily, Weekly, Monthly.
3. In CNFund UI:
   - run `Sao lưu` -> `Tạo sao lưu thủ công`.
   - verify file appears in `/app/storage/exports`.
4. Before any destructive action (restore, bulk update):
   - always create manual backup first.
5. Monthly restore drill:
   - create staging service
   - restore one selected backup
   - verify 3 outputs: dashboard totals, investor report, transaction history.

### F. Go-live checks

1. CORS:
   - ensure `API_ALLOWED_ORIGINS` only includes production frontend domain(s).
2. Secrets:
   - do not expose `API_JWT_SECRET_KEY`, admin password, OAuth files.
3. Health checks:
   - monitor `/health` at least daily.
4. Incident path:
   - if data issue occurs, freeze writes and restore from latest known-good backup.

## 11) Official references

- Railway Config as Code:
  https://docs.railway.com/guides/config-as-code
- Railway config reference:
  https://docs.railway.com/reference/config-as-code-reference
- Railway Volumes reference (including caveat: one volume per service):  
  https://docs.railway.com/volumes/reference
- Railway Volume backups (manual + schedule + restore flow):  
  https://docs.railway.com/volumes/backups
- Vercel monorepo setup with Root Directory via Dashboard:  
  https://vercel.com/docs/monorepos/
