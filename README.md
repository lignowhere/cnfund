# CNFund

CNFund hiện dùng kiến trúc:
- Frontend: Next.js (`frontend_app`)
- Backend: FastAPI (`backend_api`)
- Data nghiệp vụ: PostgreSQL (bảng `fund_*`)
- Backup: local export + upload Google Drive từ backend API

## Yêu cầu

- Python 3.11+
- Node.js 20+
- PostgreSQL

## Cài đặt nhanh

```powershell
# Backend deps
.\.venv\Scripts\python -m pip install -r backend_api/requirements.txt

# Frontend deps
cd frontend_app
npm install
cd ..
```

## Cấu hình môi trường

Tạo `.env` ở repo root từ `backend_api/.env.example` và điền tối thiểu:

```env
API_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cnfund
API_JWT_SECRET_KEY=<strong-secret>
API_ADMIN_USERNAME=admin
API_ADMIN_PASSWORD=<strong-password>
API_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Nếu cần auto backup lên Google Drive:

```env
GOOGLE_DRIVE_FOLDER_ID=<drive-folder-id-or-url>
GOOGLE_OAUTH_TOKEN_BASE64=<base64-token>
API_AUTO_BACKUP_ON_NEW_TRANSACTION=true
```

## Chạy local bằng 1 lệnh

```powershell
npm run dev
```

Mặc định:
- Frontend: `http://localhost:3000/login`
- Backend API docs: `http://127.0.0.1:8001/docs`

## Test nhanh

```powershell
.\.venv\Scripts\python -m pytest tests/test_math_audit.py
.\.venv\Scripts\python -m pytest tests/test_backend_smoke.py
.\.venv\Scripts\python -m compileall backend_api/app
```

## Migrate dữ liệu `.xlsx` vào PostgreSQL

```powershell
.\.venv\Scripts\python scripts/migrate_drive_latest_to_postgres.py --local-file "D:\Đầu tư\CNFund\data\CNFund_Backup_20260216_110200.xlsx"
```

Có thể truyền DB URL trực tiếp:

```powershell
.\.venv\Scripts\python scripts/migrate_drive_latest_to_postgres.py --database-url "<postgres-url>" --local-file "D:\...\backup.xlsx"
```

## Chạy local khi Railway không khả dụng

Nếu Railway hết hạn hoặc không truy cập được, có thể chạy hoàn toàn local với PostgreSQL cài trên máy.

**Yêu cầu:** PostgreSQL cài local + bản backup `.xlsx` mới nhất (trong `exports/` hoặc tải từ Google Drive).

```powershell
# Setup database local từ backup mới nhất (1 lệnh)
.\.venv\Scripts\python scripts/setup_local_db.py

# Hoặc chỉ định file cụ thể
.\.venv\Scripts\python scripts/setup_local_db.py --file exports/Fund_Export_20260313_manual.xlsx

# Chạy app bình thường
npm run dev
```

**Backup định kỳ** (khuyến nghị chạy hàng ngày khi hệ thống đang hoạt động):

```powershell
.\.venv\Scripts\python scripts/scheduled_backup.py
```

## Deploy

Xem chi tiết tại:
- `docs/deployment-guide.md` — tổng hợp env vars, Railway/Vercel setup, backup, rollback
- `docs/DEPLOYMENT_LOW_COST_STABLE.md` — detailed Railway + Vercel runbook
- `docs/CUTOVER_AND_ROLLBACK_PLAYBOOK.md` — release checklist + rollback

## Documentation

Toàn bộ tài liệu tại `docs/README.md`:
- `docs/project-overview-pdr.md` — business rules, fee logic, RBAC
- `docs/system-architecture.md` — architecture diagrams, API map, DB schema
- `docs/codebase-summary.md` — directory structure, key files
- `docs/project-roadmap.md` — security issues, technical debt priorities
