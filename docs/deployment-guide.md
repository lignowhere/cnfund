# Deployment Guide

_Last updated: 2026-03-13_

Tham chiếu chi tiết: `docs/DEPLOYMENT_LOW_COST_STABLE.md` và `docs/CUTOVER_AND_ROLLBACK_PLAYBOOK.md`.

---

## 1. Stack Overview

| Component | Platform | Trigger |
|-----------|----------|---------|
| Frontend | Vercel Hobby | Git push to main |
| Backend API | Railway | Git push to main |
| Database | Railway PostgreSQL | Managed |
| Backup storage | `exports/` + Google Drive | Post-transaction |

---

## 2. Environment Variables

### Backend (Railway) — prefix `API_`

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_DATABASE_URL` | YES | — | `postgresql://user:pass@host:5432/db` |
| `API_JWT_SECRET_KEY` | YES | — | Strong random string (min 32 chars). App refuses to start if blank or known-bad. |
| `API_ADMIN_USERNAME` | YES | — | Initial admin username |
| `API_ADMIN_PASSWORD` | YES | — | Initial admin password. App warns (but continues) if weak. |
| `API_ENVIRONMENT` | No | `development` | Set to `production` in prod |
| `API_ALLOWED_ORIGINS` | No | `http://localhost:3000,...` | Comma-separated CORS origins, e.g. `https://yourapp.vercel.app` |
| `API_ALLOWED_ORIGIN_REGEX` | No | local pattern | Regex for allowed origins (alternative to list) |
| `API_ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | JWT access token lifetime |
| `API_REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token lifetime |
| `API_FEATURE_TABLE_VIEW` | No | `true` | Enable table view in frontend |
| `API_FEATURE_BACKUP_RESTORE` | No | `true` | Enable backup/restore UI |
| `API_FEATURE_FEE_SAFETY` | No | `true` | Enable fee safety controls (keep true in prod) |
| `API_FEATURE_TRANSACTIONS_LOAD_MORE` | No | `true` | Paginated transaction loading |
| `API_AUTO_BACKUP_ON_NEW_TRANSACTION` | No | `true` | Auto backup after each transaction |
| `GOOGLE_DRIVE_FOLDER_ID` | No | — | Google Drive folder ID or URL for backup uploads |
| `GOOGLE_OAUTH_TOKEN_BASE64` | No | — | Base64-encoded OAuth token JSON (from `encode_oauth_token.py`) |

### Frontend (Vercel)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | YES | `https://<railway-backend-domain>/api/v1` |

---

## 3. First-Time Railway Setup

```
1. Create Railway project
2. Add service → Deploy from GitHub repo (root directory)
3. Enable Config as Code → uses railway.toml
4. Add PostgreSQL plugin to same project
5. Set all required env vars (section 2)
6. Optional: mount volume at /app/storage for persistent exports
7. Redeploy → verify https://<backend>/health returns {"status":"ok"}
8. Verify https://<backend>/docs for API explorer
```

If build fails with "python: not found":
```
Check railway.toml [build] uses Dockerfile builder
Railway → Service → Settings → Builder: Dockerfile
```

---

## 4. First-Time Vercel Setup

```
1. Import repo to Vercel
2. Root Directory: frontend_app
3. Framework: Next.js (auto-detected)
4. Add env var: NEXT_PUBLIC_API_BASE_URL=https://<railway-backend-domain>/api/v1
5. Deploy
6. Test: /login, dashboard, investors
```

---

## 5. Data Migration (xlsx → PostgreSQL)

Use when migrating from backup file to a fresh DB:

```powershell
.\.venv\Scripts\python scripts/migrate_drive_latest_to_postgres.py `
  --database-url "postgresql://..." `
  --local-file "D:\path\to\CNFund_Backup_YYYYMMDD_HHMMSS.xlsx"
```

Script flow:
1. Copies file to `exports/`
2. Parses Excel sheets (investors, tranches, transactions, fee_records)
3. Writes to `fund_*` tables in PostgreSQL

---

## 6. Google Drive Backup Setup

1. Create Google Cloud project, enable Drive API
2. Create OAuth2 credentials (Desktop app type)
3. Run locally: `python scripts/encode_oauth_token.py` (follows OAuth flow, creates `token.json`)
4. Base64-encode: `python -c "import base64; print(base64.b64encode(open('token.json','rb').read()).decode())"`
5. Set `GOOGLE_OAUTH_TOKEN_BASE64` in Railway env vars
6. Set `GOOGLE_DRIVE_FOLDER_ID` to target folder ID or URL

**Security note:** Keep `token.pickle` and `token.json` out of git (already in `.gitignore`). Rotate credentials if accidentally committed.

---

## 7. Standard Deployment Flow

```
# Before deploying:
cd frontend_app && npm run lint && npm run build
cd .. && .venv/Scripts/python -m compileall backend_api/app
.venv/Scripts/python -m pytest tests/test_math_audit.py
.venv/Scripts/python -m pytest tests/test_backend_smoke.py

# Deploy:
git push origin main
# → Railway auto-deploys backend
# → Vercel auto-deploys frontend

# Verify:
curl https://<backend>/health
# Run smoke checklist (see below)
```

---

## 8. Smoke Test Checklist (Post-Deploy)

- [ ] `GET /health` returns `{"status":"ok"}`
- [ ] Login + refresh token flow works
- [ ] Create investor succeeds
- [ ] Add deposit transaction succeeds
- [ ] Fee preview/apply works with safety controls
- [ ] Manual backup + restore confirmation works
- [ ] Reports page loads with data

---

## 9. Rollback (<15 minutes)

**Frontend (Vercel):**
- Vercel Dashboard → Deployments → Previous deployment → "Promote to Production"

**Backend (Railway):**
- Railway Dashboard → Service → Deployments → Previous deployment → "Redeploy"
- OR: `railway redeploy -s <service-id> -y`

**Emergency flag disabling:**
```env
API_FEATURE_BACKUP_RESTORE=false    # if backup restore is causing issues
# Keep API_FEATURE_FEE_SAFETY=true  # always keep fee safety on
```

---

## 10. Backup Policy (Minimum)

1. **Railway PostgreSQL:** Enable Daily + Weekly backup (Railway dashboard → Database → Backups)
2. **Pre-risk operations:** Trigger manual backup via API or UI before applying fees or mass operations
3. **Monthly:** Run restore drill on staging/local environment
4. **Google Drive:** Auto-upload enabled via `API_AUTO_BACKUP_ON_NEW_TRANSACTION=true`

### Scheduled Backup Script

Chạy định kỳ để tạo backup `.xlsx` từ production database:

```powershell
# Backup thủ công
.\.venv\Scripts\python scripts/scheduled_backup.py

# Hoặc chỉ định DB URL
.\.venv\Scripts\python scripts/scheduled_backup.py --database-url "postgresql://..."

# Dry run (kiểm tra config)
.\.venv\Scripts\python scripts/scheduled_backup.py --dry-run
```

**Windows Task Scheduler:**
```
Action: Start a program
Program: D:\Đầu tư\CNFund\.venv\Scripts\python.exe
Arguments: scripts/scheduled_backup.py
Start in: D:\Đầu tư\CNFund
Trigger: Daily at 00:00
```

**Linux cron (nếu chạy trên server):**
```cron
0 0 * * * cd /path/to/CNFund && .venv/bin/python scripts/scheduled_backup.py >> logs/backup.log 2>&1
```

Backup được lưu tại `exports/Fund_Export_*_manual_scheduled.xlsx` và auto-upload Google Drive nếu credentials đã cấu hình.

---

## 11. Chạy Local Khi Railway Không Khả Dụng

Nếu Railway hết hạn hoặc không truy cập được, có thể chạy hoàn toàn trên máy local.

**Yêu cầu:** PostgreSQL cài local + bản backup `.xlsx` mới nhất.

```powershell
# 1-command setup: tạo DB + restore từ backup mới nhất
.\.venv\Scripts\python scripts/setup_local_db.py

# Hoặc chỉ định file cụ thể
.\.venv\Scripts\python scripts/setup_local_db.py --file exports/Fund_Export_20260313.xlsx

# Custom PostgreSQL config
.\.venv\Scripts\python scripts/setup_local_db.py --pg-user myuser --pg-password mypass --pg-port 5433
```

Script sẽ:
1. Kiểm tra PostgreSQL connection
2. Tạo database `cnfund` nếu chưa có
3. Restore toàn bộ dữ liệu từ backup
4. In ra `API_DATABASE_URL` để thêm vào `.env`

Sau đó chạy `npm run dev` bình thường.

---

## 12. Local Development

```powershell
# Single command (concurrently runs backend + frontend):
npm run dev

# Backend only:
.venv/Scripts/uvicorn backend_api.app.main:app --host 127.0.0.1 --port 8001 --reload

# Frontend only:
cd frontend_app && npm run dev
```

Endpoints:
- Frontend: `http://localhost:3000`
- Backend API: `http://127.0.0.1:8001/docs`
