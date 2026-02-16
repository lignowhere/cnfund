# CNFund Deployment Plan (Low Cost + Stable)

## 1) Kiến trúc đích

- Frontend: Vercel Hobby (`frontend_app`)
- Backend API: Railway (`backend_api`)
- Database: Railway PostgreSQL
- Dữ liệu nghiệp vụ: PostgreSQL (`fund_investors`, `fund_tranches`, `fund_transactions`, `fund_fee_records`)
- Backup:
  - PostgreSQL backups trên Railway
  - Backup thủ công / restore qua API
  - Auto backup sau giao dịch mới (local + upload Google Drive nếu có cấu hình)

## 2) Biến môi trường backend

```env
API_ENVIRONMENT=production
API_DATABASE_URL=${{Postgres.DATABASE_URL}}
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
API_AUTO_BACKUP_ON_NEW_TRANSACTION=true
GOOGLE_DRIVE_FOLDER_ID=<drive-folder-id-or-url>
GOOGLE_OAUTH_TOKEN_BASE64=<base64-token-from-token.pickle>
```

Ghi chú:
- Runtime chính thức là PostgreSQL-only.
- `API_POSTGRES_BOOTSTRAP_FROM_CSV=true` chỉ dùng một lần khi DB đang rỗng.

## 3) Railway click-by-click

1. Tạo project trên Railway.
2. Deploy repo này (service ở repo root).
3. Bật Config as Code, dùng `railway.toml`.
4. Thêm PostgreSQL service trong cùng project.
5. Set biến môi trường backend như mục 2.
6. (Tùy chọn) thêm volume mount `/app/storage` để giữ export file lâu dài.
7. Redeploy backend.
8. Verify:
   - `https://<backend-domain>/health`
   - `https://<backend-domain>/docs`

Nếu build lỗi `python: not found`:
1. Kiểm tra service đang dùng `railway.toml` mới nhất.
2. `[build]` phải là Dockerfile builder.
3. Redeploy lại:

```powershell
railway redeploy -s <backend-service-id> -y
```

## 4) One-time CSV -> PostgreSQL bootstrap

Khi đã có 4 file CSV ở `backend_api/data/` và DB rỗng:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\railway_bootstrap_postgres_once.ps1 -ServiceId <backend-service-id>
```

Flow script:
1. Set `API_POSTGRES_BOOTSTRAP_FROM_CSV=true`
2. Upload/deploy để bootstrap dữ liệu
3. Set lại `API_POSTGRES_BOOTSTRAP_FROM_CSV=false`
4. Redeploy chế độ thường

## 5) Migrate trực tiếp từ file backup `.xlsx` local

```powershell
.\.venv\Scripts\python scripts/migrate_drive_latest_to_postgres.py --database-url "<postgres-url>" --local-file "D:\Đầu tư\CNFund\data\CNFund_Backup_20260216_110200.xlsx"
```

Script sẽ:
1. Copy file vào `exports/`
2. Parse sheet backup
3. Ghi dữ liệu vào bảng `fund_*` trong PostgreSQL

## 6) Vercel click-by-click

1. Import cùng repo lên Vercel.
2. Root directory: `frontend_app`.
3. Set env var:

```env
NEXT_PUBLIC_API_BASE_URL=https://<your-railway-backend-domain>/api/v1
```

4. Deploy.
5. Verify các route chính: `/login`, dashboard, investors, transactions, reports.

## 7) Chính sách backup tối thiểu

1. Railway PostgreSQL: bật backup Daily/Weekly/Monthly.
2. Trước thao tác rủi ro cao: tạo manual backup qua API.
3. Mỗi tháng: chạy restore drill trên môi trường staging.

## 8) Tài liệu tham chiếu

- Railway Config as Code:
  https://docs.railway.com/guides/config-as-code
- Railway config reference:
  https://docs.railway.com/reference/config-as-code-reference
- Vercel monorepo setup:
  https://vercel.com/docs/monorepos/
