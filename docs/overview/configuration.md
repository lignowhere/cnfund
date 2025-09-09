# Cấu Hình Hệ Thống

## Cấu Hình Cơ Bản

### File config.py

File `config.py` chứa các cấu hình cốt lõi của hệ thống:

```python
# Cấu hình Streamlit Page
PAGE_CONFIG = {
    "page_title": "Fund Management System",
    "page_icon": "💰",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Cấu hình phí
PERFORMANCE_FEE_RATE = 0.20  # 20% phí hiệu suất
MANAGEMENT_FEE_RATE = 0.02   # 2% phí quản lý (nếu áp dụng)

# Cấu hình validation
MIN_INVESTMENT = 1000000     # Số tiền đầu tư tối thiểu
MAX_INVESTMENT = 100000000   # Số tiền đầu tư tối đa
```

### Variables Môi Trường

#### File .env
```env
# Database
DATABASE_URL=postgresql://postgres:password@host:port/database
DB_TIMEOUT=30

# Security
ADMIN_PASSWORD=your_secure_password
SESSION_TIMEOUT=3600

# Google Drive (Optional)
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
GOOGLE_DRIVE_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=app.log
```

#### File .streamlit/secrets.toml
```toml
# Database Configuration
database_url = "postgresql://postgres:password@host:port/database"

# Admin Configuration  
admin_password = "your_secure_admin_password"

# Google Drive Configuration
[google_drive]
enabled = true
folder_id = "your_google_drive_folder_id"
credentials_json = """
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
  "client_email": "service-account@project.iam.gserviceaccount.com",
  "client_id": "client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
"""
```

## Cấu Hình Database

### Supabase PostgreSQL

#### Connection Settings
```python
# Trong supabase_data_handler.py
ENGINE_CONFIG = {
    "pool_pre_ping": True,
    "connect_args": {
        "sslmode": "require",
        "connect_timeout": 5,
        "application_name": "FundManagerApp"
    },
    "pool_size": 10,
    "max_overflow": 20
}
```

#### Table Schemas

Hệ thống tự động tạo các bảng với schema sau:

```sql
-- Bảng Investors
CREATE TABLE investors (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    email VARCHAR(255),
    join_date DATE NOT NULL,
    is_fund_manager BOOLEAN DEFAULT FALSE
);

-- Bảng Tranches  
CREATE TABLE tranches (
    investor_id INTEGER,
    tranche_id VARCHAR(50) PRIMARY KEY,
    entry_date TIMESTAMP NOT NULL,
    entry_nav DECIMAL(15,6) NOT NULL,
    units DECIMAL(15,6) NOT NULL,
    original_invested_value DECIMAL(15,2) NOT NULL,
    hwm DECIMAL(15,6),
    original_entry_date TIMESTAMP,
    original_entry_nav DECIMAL(15,6),
    cumulative_fees_paid DECIMAL(15,2) DEFAULT 0,
    FOREIGN KEY (investor_id) REFERENCES investors(id)
);

-- Bảng Transactions
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    investor_id INTEGER NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    nav_after_transaction DECIMAL(15,6) NOT NULL,
    units_change DECIMAL(15,6) NOT NULL,
    price_per_unit DECIMAL(15,6) NOT NULL,
    notes TEXT,
    FOREIGN KEY (investor_id) REFERENCES investors(id)
);

-- Bảng Fee Records
CREATE TABLE fee_records (
    id SERIAL PRIMARY KEY,
    investor_id INTEGER NOT NULL,
    fee_period VARCHAR(10) NOT NULL,
    fee_amount DECIMAL(15,2) NOT NULL,
    units_transferred DECIMAL(15,6) NOT NULL,
    calculated_date TIMESTAMP NOT NULL,
    nav_at_calculation DECIMAL(15,6) NOT NULL,
    performance_percentage DECIMAL(10,6),
    FOREIGN KEY (investor_id) REFERENCES investors(id)
);
```

## Cấu Hình UI/UX

### Streamlit Configuration

#### File .streamlit/config.toml
```toml
[global]
developmentMode = false

[server]
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"  
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
```

### Custom Styling

File `styles.py` chứa custom CSS:

```python
# Mobile-responsive design
MOBILE_CSS = """
<style>
@media (max-width: 768px) {
    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}
</style>
"""

# Custom colors and themes
CUSTOM_THEME = {
    "primary": "#FF6B6B",
    "secondary": "#4ECDC4", 
    "success": "#45B7D1",
    "warning": "#FFA07A",
    "error": "#FF6B6B"
}
```

## Cấu Hình Bảo Mật

### Authentication

```python
# security_manager.py
SECURITY_CONFIG = {
    "session_timeout": 3600,  # 1 hour
    "max_login_attempts": 3,
    "password_min_length": 8,
    "require_strong_password": True
}

# Audit logging
AUDIT_CONFIG = {
    "log_transactions": True,
    "log_fee_calculations": True,
    "log_data_changes": True,
    "retention_days": 365
}
```

### Data Validation

```python
# data_utils.py
VALIDATION_RULES = {
    "phone_regex": r"^(\+84|0)[0-9]{9,10}$",
    "email_regex": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "amount_min": 0,
    "amount_max": 999999999999,
    "name_max_length": 255
}
```

## Cấu Hình Performance

### Caching Strategy

```python
# app.py - Streamlit caching
@st.cache_resource
def load_data_handler():
    return SupabaseDataHandler()

@st.cache_data(ttl=300)  # 5 minutes TTL
def get_investor_stats(nav_value):
    return fm.get_investor_statistics(nav_value)
```

### Database Optimization

```python
# supabase_data_handler.py
CONNECTION_POOL = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 3600
}
```

## Cấu Hình Logging

### Logging Configuration

```python
# comprehensive_debug.py
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": [
        {
            "type": "file",
            "filename": "logs/app.log",
            "max_bytes": 10485760,  # 10MB
            "backup_count": 5
        },
        {
            "type": "console",
            "level": "WARNING"
        }
    ]
}
```

## Cấu Hình Backup

### Automated Backups

```python
# backup_config.py
BACKUP_SETTINGS = {
    "enabled": True,
    "schedule": "daily",  # daily, weekly, monthly
    "retention_days": 30,
    "backup_location": "backups/",
    "include_exports": True,
    "compress": True
}
```

### Google Drive Integration

```python
# google_drive_manager.py
DRIVE_CONFIG = {
    "upload_timeout": 300,
    "chunk_size": 1024*1024,  # 1MB chunks
    "retry_attempts": 3,
    "folder_structure": {
        "reports": "Reports",
        "backups": "Backups", 
        "exports": "Exports"
    }
}
```

## Environment-Specific Configs

### Development
```python
DEV_CONFIG = {
    "debug": True,
    "auto_reload": True,
    "show_debug_info": True,
    "mock_data": False
}
```

### Production
```python
PROD_CONFIG = {
    "debug": False,
    "auto_reload": False,
    "show_debug_info": False,
    "enable_monitoring": True,
    "strict_validation": True
}
```

### Testing
```python
TEST_CONFIG = {
    "use_test_db": True,
    "mock_external_apis": True,
    "fast_calculations": True,
    "skip_heavy_operations": True
}
```

## Monitoring và Alerts

### Health Checks

```python
HEALTH_CHECK_CONFIG = {
    "database_timeout": 5,
    "api_timeout": 10,
    "check_interval": 60,
    "alert_thresholds": {
        "response_time": 2.0,
        "error_rate": 0.05,
        "cpu_usage": 0.8
    }
}
```

### Alert Configuration

```python
ALERT_CONFIG = {
    "email_alerts": True,
    "slack_webhook": "https://hooks.slack.com/...",
    "alert_conditions": [
        "database_connection_failed",
        "high_error_rate", 
        "performance_degradation"
    ]
}
```