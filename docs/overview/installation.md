# Hướng Dẫn Cài Đặt Hệ Thống

## Yêu Cầu Hệ Thống

### Phần Mềm Cần Thiết
- **Python**: 3.8 hoặc cao hơn
- **pip**: Package manager cho Python
- **Git**: Version control system
- **PostgreSQL**: Database (thông qua Supabase)

### Tài Khoản Cần Thiết
- **Supabase Account**: Để tạo PostgreSQL database
- **Google Drive API**: Để lưu trữ báo cáo (tùy chọn)

## Cài Đặt Cơ Bản

### 1. Clone Repository

```bash
git clone <repository-url>
cd CNFund
```

### 2. Tạo Virtual Environment

```bash
# Tạo virtual environment
python -m venv .venv

# Kích hoạt virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### 3. Cài Đặt Dependencies

```bash
pip install -r requirements.txt
```

## Cấu Hình Database

### 1. Tạo Supabase Project

1. Truy cập [Supabase.com](https://supabase.com)
2. Tạo tài khoản và project mới
3. Lấy Database URL từ Settings > Database

### 2. Cấu Hình Environment Variables

Tạo file `.env` trong thư mục gốc:

```env
DATABASE_URL=postgresql://postgres:[password]@[host]:[port]/postgres
```

### 3. Cấu Hình Streamlit Secrets

Tạo file `.streamlit/secrets.toml`:

```toml
database_url = "postgresql://postgres:[password]@[host]:[port]/postgres"
admin_password = "your_admin_password"

# Google Drive (tùy chọn)
[google_drive]
credentials_json = """
{
  "type": "service_account",
  "project_id": "your-project-id",
  ...
}
"""
```

## Cài Đặt Google Drive Integration (Tùy chọn)

### 1. Tạo Google Cloud Project

1. Truy cập [Google Cloud Console](https://console.cloud.google.com)
2. Tạo project mới
3. Enable Google Drive API

### 2. Tạo Service Account

1. Vào IAM & Admin > Service Accounts
2. Tạo service account mới
3. Tải JSON credentials file

### 3. Cấu Hình Credentials

Sao chép nội dung JSON file vào `secrets.toml` như trên.

## Khởi Chạy Ứng Dụng

### 1. Database Initialization

Khi chạy lần đầu, hệ thống sẽ tự động tạo các bảng cần thiết.

### 2. Chạy Streamlit

```bash
streamlit run app.py
```

### 3. Truy Cập Ứng Dụng

Mở browser và truy cập: `http://localhost:8501`

## Xác Minh Cài Đặt

### 1. Kiểm Tra Database Connection

- Truy cập ứng dụng
- Kiểm tra thông báo kết nối database ở sidebar

### 2. Test Chức Năng Cơ Bản

- Thử thêm một nhà đầu tư test
- Kiểm tra các trang báo cáo
- Test login với admin password

### 3. Kiểm Tra Google Drive (nếu có)

- Thử export một báo cáo
- Kiểm tra file có được tải lên Drive không

## Troubleshooting

### Lỗi Kết Nối Database

```
❌ Không thể kết nối tới Database
```

**Giải pháp:**
- Kiểm tra DATABASE_URL trong secrets.toml
- Đảm bảo Supabase project đang active
- Kiểm tra firewall/network connection

### Lỗi Missing Dependencies

```
ModuleNotFoundError: No module named 'xxx'
```

**Giải pháp:**
```bash
pip install -r requirements.txt --force-reinstall
```

### Lỗi Google Drive API

```
Error: Google Drive authentication failed
```

**Giải pháp:**
- Kiểm tra service account credentials
- Đảm bảo Google Drive API đã được enable
- Xem lại format JSON trong secrets.toml

### Lỗi Streamlit Port

```
Port 8501 is already in use
```

**Giải pháp:**
```bash
streamlit run app.py --server.port 8502
```

## Development Setup

### 1. Cài Đặt Dev Dependencies

```bash
pip install pytest black flake8 mypy
```

### 2. Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

### 3. Run Tests

```bash
pytest
```

## Production Deployment

### 1. Streamlit Cloud

1. Push code lên GitHub
2. Connect GitHub repo với Streamlit Cloud
3. Cấu hình secrets trên Streamlit Cloud dashboard

### 2. Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

### 3. Environment Variables

Đảm bảo các environment variables được set:
- `DATABASE_URL`
- `ADMIN_PASSWORD`
- Google Drive credentials (nếu sử dụng)

## Cấu Hình Bảo Mật

### 1. Database Security

- Sử dụng SSL connection
- Hạn chế IP access
- Strong password policy

### 2. Application Security

- Đổi admin password mặc định
- Enable HTTPS cho production
- Regular backup database

### 3. Monitoring

- Setup health checks
- Monitor database performance
- Log important actions

## Backup và Recovery

### 1. Database Backup

```bash
# Manual backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

### 2. Application Data

- Regular export của data qua Excel
- Git backup cho code changes
- Google Drive backup cho reports