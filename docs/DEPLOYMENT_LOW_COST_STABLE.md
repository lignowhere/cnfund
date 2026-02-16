# CNFund Deploy Plan (PostgreSQL Business Data)

## 1) Target architecture

- Frontend: Vercel Hobby (Next.js)
- Backend API: Railway (FastAPI)
- Database: Railway PostgreSQL
- Business data: PostgreSQL tables (`fund_investors`, `fund_tranches`, `fund_transactions`, `fund_fee_records`)
- Auth/Audit: PostgreSQL tables (`users`, `refresh_tokens`, `audit_logs`)
- Backups:
  - Railway PostgreSQL backups
  - App manual backup/restore (`/api/v1/backups/manual`, `/api/v1/backups/restore`)
  - Optional Railway Volume only for export files (`/app/storage/exports`)

## 2) Environment variables (backend)

```env
API_ENVIRONMENT=production
API_DATABASE_URL=${{Postgres.DATABASE_URL}}
API_CNFUND_DATA_SOURCE=postgres
API_POSTGRES_BOOTSTRAP_FROM_CSV=false
API_POSTGRES_SEED_DIR=
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

Notes:
- `API_CNFUND_DATA_SOURCE=postgres` is now the primary mode.
- `API_POSTGRES_BOOTSTRAP_FROM_CSV=true` is only for one-time migration when DB is empty.

## 3) Railway click-by-click

1. Create project on Railway.
2. Deploy this repository (service at repo root).
3. Enable `Config as Code` and select `/railway.toml`.
4. Add PostgreSQL service in same project.
5. Add backend variables from section 2.
6. (Optional) Add a volume and mount at `/app/storage` to persist export files.
7. Redeploy backend.
8. Verify:
   - `https://<backend-domain>/health`
   - `https://<backend-domain>/docs`

If you ever see `python: not found` in build:
1. Ensure backend service uses latest `railway.toml`.
2. Confirm `[build]` uses:
   - `builder = "DOCKERFILE"`
   - `dockerfilePath = "Dockerfile"`
3. Redeploy:
   - `railway redeploy -s <backend-service-id> -y`

## 4) One-time CSV -> PostgreSQL migration

Use when you already have real CSV data and want to import once into PostgreSQL.

Preconditions:
- 4 real CSV files are in `backend_api/data/`:
  - `investors.csv`
  - `tranches.csv`
  - `transactions.csv`
  - `fee_records.csv`
- DB is empty (or you accept overwrite by restore process later).

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\railway_bootstrap_postgres_once.ps1 -ServiceId <backend-service-id>
```

Script flow:
1. Set `API_CNFUND_DATA_SOURCE=postgres`
2. Set `API_POSTGRES_BOOTSTRAP_FROM_CSV=true`
3. Run `railway up --no-gitignore` once to upload local backend source + CSV and import into Postgres (if DB is empty)
4. Set `API_POSTGRES_BOOTSTRAP_FROM_CSV=false`
5. Redeploy again to lock normal mode

Optional:
- If CSV already exists in deployed source and you do not want local upload:
  - add `-SkipLocalUpload`

## 4.1) Migrate trực tiếp từ file backup `.xlsx` local vào PostgreSQL

Không cần tải từ Google Drive nếu bạn đã có file local, ví dụ:
`D:\Đầu tư\CNFund\data\CNFund_Backup_20260216_110200.xlsx`

```powershell
$dbUrl = (railway variable list -s <postgres-service-id> -k | Select-String '^DATABASE_PUBLIC_URL=').ToString().Split('=',2)[1]
.\.venv\Scripts\python scripts\migrate_drive_latest_to_postgres.py --database-url "$dbUrl" --local-file "D:\Đầu tư\CNFund\data\CNFund_Backup_20260216_110200.xlsx"
```

Script sẽ:
1. Copy file vào `exports/` (để dùng restore flow thống nhất).
2. Parse sheet theo nhiều format cũ/mới (`Investors`, `Tranches`, `Transactions`, `Fee Records`...).
3. Ghi đè dữ liệu nghiệp vụ vào các bảng `fund_*` trong PostgreSQL.

## 5) Vercel click-by-click

1. Import same repo into Vercel.
2. Set project root directory: `frontend_app`.
3. Add env var:

```env
NEXT_PUBLIC_API_BASE_URL=https://<your-railway-backend-domain>/api/v1
```

4. Deploy.
5. Verify:
   - `/login`
   - dashboard
   - investors
   - transactions
   - reports

## 6) Backup policy (critical)

1. Railway PostgreSQL -> Backups:
   - enable Daily, Weekly, Monthly.
2. In app:
   - run manual backup before destructive operations.
3. Monthly restore drill:
   - restore on staging
   - verify dashboard totals, investor report, transaction history.

## 7) Notes

- Google Drive mode (`API_CNFUND_DATA_SOURCE=drive`) is still legacy and should not be primary production storage.
- PostgreSQL is now the canonical data source for fund business data in this repo.

## 8) References

- Railway Config as Code:
  https://docs.railway.com/guides/config-as-code
- Railway config reference:
  https://docs.railway.com/reference/config-as-code-reference
- Vercel monorepo setup:
  https://vercel.com/docs/monorepos/
