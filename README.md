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

## Deploy

Xem chi tiết tại:
- `docs/DEPLOYMENT_LOW_COST_STABLE.md`
- `docs/CUTOVER_AND_ROLLBACK_PLAYBOOK.md`
