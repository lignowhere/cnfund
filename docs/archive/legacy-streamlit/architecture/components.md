# Chi Tiết Components Hệ Thống

## Sơ Đồ Components

```
┌───────────────────────────────────────────────────────────────┐
│                      FRONTEND COMPONENTS                      │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Main App      │     Pages       │       UI Components         │
│   (app.py)      │                 │                             │
│                 │ ┌─────────────┐ │ ┌─────────┐ ┌─────────────┐ │
│ ┌─────────────┐ │ │ investor_   │ │ │ Styles  │ │ Sidebar     │ │
│ │ Bootstrap   │ │ │ page.py     │ │ │ Manager │ │ Manager     │ │
│ │ & Config    │ │ └─────────────┘ │ └─────────┘ └─────────────┘ │
│ └─────────────┘ │ ┌─────────────┐ │                             │
│                 │ │transaction_ │ │ ┌─────────┐ ┌─────────────┐ │
│ ┌─────────────┐ │ │ page.py     │ │ │Security │ │Progressive  │ │
│ │ Lazy        │ │ └─────────────┘ │ │Auth     │ │Loader       │ │
│ │ Loading     │ │ ┌─────────────┐ │ └─────────┘ └─────────────┘ │
│ └─────────────┘ │ │fee_page_    │ │                             │
│                 │ │enhanced.py  │ │                             │
│                 │ └─────────────┘ │                             │
│                 │ ┌─────────────┐ │                             │
│                 │ │report_page_ │ │                             │
│                 │ │enhanced.py  │ │                             │
│                 │ └─────────────┘ │                             │
└─────────────────┴─────────────────┴─────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC COMPONENTS                  │
├─────────────────┬─────────────────┬─────────────────────────────┤
│ Core Services   │  Domain Logic   │      Utilities              │
│                 │                 │                             │
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────┐ ┌─────────────┐ │
│ │Enhanced     │ │ │ Fee         │ │ │ Data    │ │ Validation  │ │
│ │Fund Manager │ │ │ Calculator  │ │ │ Utils   │ │ Utils       │ │
│ └─────────────┘ │ └─────────────┘ │ └─────────┘ └─────────────┘ │
│                 │ ┌─────────────┐ │                             │
│ ┌─────────────┐ │ │Performance  │ │ ┌─────────┐ ┌─────────────┐ │
│ │Security     │ │ │Calculator   │ │ │Number   │ │Email/Phone  │ │
│ │Manager      │ │ └─────────────┘ │ │Format   │ │Validation   │ │
│ └─────────────┘ │ ┌─────────────┐ │ └─────────┘ └─────────────┘ │
│                 │ │ Tranche     │ │                             │
│ ┌─────────────┐ │ │ Manager     │ │ ┌─────────┐ ┌─────────────┐ │
│ │Audit        │ │ └─────────────┘ │ │Date     │ │Error        │ │
│ │Logger       │ │                 │ │Utils    │ │Handlers     │ │
│ └─────────────┘ │                 │ └─────────┘ └─────────────┘ │
└─────────────────┴─────────────────┴─────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                      DATA COMPONENTS                          │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Data Models   │  Data Handlers  │    External Services        │
│                 │                 │                             │
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────┐ ┌─────────────┐ │
│ │ Investor    │ │ │Supabase     │ │ │Google   │ │ Backup      │ │
│ │ Model       │ │ │Data Handler │ │ │Drive    │ │ Manager     │ │
│ └─────────────┘ │ └─────────────┘ │ │Manager  │ └─────────────┘ │
│ ┌─────────────┐ │ ┌─────────────┐ │ └─────────┘                 │
│ │ Tranche     │ │ │Enhanced     │ │ ┌─────────┐ ┌─────────────┐ │
│ │ Model       │ │ │Data Handler │ │ │Realtime │ │File         │ │
│ └─────────────┘ │ └─────────────┘ │ │Sync Fix │ │Manager      │ │
│ ┌─────────────┐ │ ┌─────────────┐ │ └─────────┘ └─────────────┘ │
│ │Transaction  │ │ │Database     │ │                             │
│ │ Model       │ │ │Optimization │ │                             │
│ └─────────────┘ │ └─────────────┘ │                             │
│ ┌─────────────┐ │                 │                             │
│ │FeeRecord    │ │                 │                             │
│ │ Model       │ │                 │                             │
│ └─────────────┘ │                 │                             │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

## Frontend Components

### 1. Main Application (app.py)

#### Bootstrap Component
```python
class AppBootstrap:
    """Khởi tạo ứng dụng với lazy loading"""
    
    @staticmethod
    @st.cache_resource
    def load_config():
        from config import PAGE_CONFIG
        return PAGE_CONFIG
    
    @staticmethod
    @st.cache_resource
    def load_data_handler():
        return SupabaseDataHandler()
    
    @staticmethod
    @st.cache_resource
    def load_fund_manager():
        return EnhancedFundManager
```

#### Configuration Manager
```python
class ConfigManager:
    """Quản lý cấu hình toàn cục"""
    
    - PAGE_CONFIG: Streamlit page settings
    - DATABASE_CONFIG: Connection settings
    - UI_CONFIG: Theme và styling
    - PERFORMANCE_CONFIG: Caching settings
```

### 2. Page Components

#### Investor Management Page
```python
class InvestorPage:
    """Component quản lý nhà đầu tư"""
    
    def render_add_investor_form():
        """Form thêm nhà đầu tư mới"""
    
    def render_investor_list():
        """Danh sách nhà đầu tư với edit capabilities"""
    
    def render_investor_status():
        """Trạng thái chi tiết từng nhà đầu tư"""
```

#### Transaction Management Page
```python
class TransactionPage:
    """Component quản lý giao dịch"""
    
    def render_add_transaction():
        """Form thêm giao dịch nạp/rút"""
    
    def render_nav_update():
        """Form cập nhật Total NAV"""
        
    def render_fund_manager_withdrawal():
        """Form rút tiền cho Fund Manager"""
    
    def render_transaction_history():
        """Lịch sử giao dịch với filters"""
    
    def render_delete_transaction():
        """Xóa giao dịch với confirmation"""
```

#### Fee Calculation Page
```python
class FeePage:
    """Component tính toán phí"""
    
    def render_fee_calculation_preview():
        """Preview phí trước khi apply"""
    
    def render_fee_details():
        """Chi tiết cách tính phí"""
    
    def render_individual_fee_calculator():
        """Tính phí cho từng nhà đầu tư"""
    
    def apply_fees():
        """Áp dụng phí sau confirmation"""
```

#### Reporting Page  
```python
class ReportPage:
    """Component báo cáo và thống kê"""
    
    def render_statistics_tab():
        """Thống kê tổng quan"""
    
    def render_lifetime_performance():
        """Performance analysis"""
    
    def render_fee_history():
        """Lịch sử phí đã thu"""
    
    def render_fund_manager_dashboard():
        """Dashboard cho Fund Manager"""
    
    def export_excel_report():
        """Export báo cáo Excel"""
```

### 3. UI Components

#### Styles Manager
```python
class StylesManager:
    """Quản lý CSS và themes"""
    
    def apply_custom_css():
        """Apply custom styling"""
    
    def get_mobile_responsive_css():
        """Mobile-friendly CSS"""
    
    def get_chart_styling():
        """Styling cho charts và graphs"""
```

#### Sidebar Manager
```python
class SidebarManager:
    """Quản lý sidebar navigation"""
    
    def render_navigation():
        """Navigation menu"""
    
    def render_status_indicators():
        """Database connection status"""
    
    def render_admin_controls():
        """Admin login/logout controls"""
```

#### Progressive Loader
```python
class ProgressiveLoader:
    """Loading states và progress indicators"""
    
    def show_loading_spinner():
        """Loading animation"""
    
    def show_progress_bar(progress):
        """Progress bar for operations"""
    
    def show_data_loading_placeholder():
        """Skeleton loading for data"""
```

## Business Logic Components

### 1. Core Services

#### Enhanced Fund Manager
```python
class EnhancedFundManager:
    """Core business logic engine"""
    
    # Constructor và initialization
    def __init__(self, data_handler):
        self.data_handler = data_handler
        self.investors = []
        self.tranches = []
        self.transactions = []
        self.fee_records = []
    
    # Data management
    def load_data():
        """Load tất cả data từ database"""
    
    def save_data():
        """Save tất cả data về database"""
    
    # Investor operations
    def add_investor(name, phone, address, email):
        """Thêm nhà đầu tư mới với validation"""
    
    def update_investor_info(investor_id, updates):
        """Cập nhật thông tin nhà đầu tư"""
    
    def get_investor_statistics(total_nav):
        """Thống kê chi tiết cho từng nhà đầu tư"""
    
    # Transaction operations  
    def add_transaction(investor_id, type, amount, date, new_nav):
        """Xử lý giao dịch nạp/rút với tranche management"""
    
    def fund_manager_withdrawal(amount, withdrawal_type):
        """Xử lý rút tiền cho Fund Manager"""
    
    # Fee calculations
    def calculate_fees_preview(year, end_date, final_nav):
        """Preview tính phí trước khi apply"""
    
    def apply_fees(year, end_date, final_nav):
        """Áp dụng phí sau confirmation"""
    
    def calculate_individual_fee(investor_id, calc_date, nav):
        """Tính phí cho nhà đầu tư cụ thể"""
```

#### Security Manager
```python
class SecurityManager:
    """Quản lý bảo mật và authentication"""
    
    def authenticate_admin(password):
        """Xác thực admin password"""
    
    def check_session_validity():
        """Kiểm tra session timeout"""
    
    def log_audit_event(event_type, details):
        """Ghi audit log"""
    
    def validate_permissions(action):
        """Kiểm tra quyền thực hiện action"""
```

#### Audit Logger
```python
class AuditLogger:
    """Ghi log cho các hoạt động quan trọng"""
    
    def log_transaction(transaction_details):
        """Log giao dịch"""
    
    def log_fee_calculation(fee_details):
        """Log tính phí"""
    
    def log_data_change(change_details):
        """Log thay đổi data"""
    
    def generate_audit_report():
        """Tạo báo cáo audit"""
```

### 2. Domain Logic

#### Fee Calculator
```python
class FeeCalculator:
    """Engine tính toán phí hiệu suất"""
    
    def calculate_performance_fee(tranche, current_nav, fee_rate):
        """Tính phí hiệu suất cho một tranche"""
    
    def update_high_water_mark(tranche, current_performance):
        """Cập nhật High Water Mark"""
    
    def calculate_fee_for_investor(investor, tranches, current_nav):
        """Tính tổng phí cho một nhà đầu tư"""
```

#### Performance Calculator
```python
class PerformanceCalculator:
    """Tính toán hiệu suất đầu tư"""
    
    def calculate_lifetime_performance(investor, tranches, current_nav):
        """Tính performance trọn đời"""
    
    def calculate_period_performance(investor, start_date, end_date):
        """Tính performance trong khoảng thời gian"""
    
    def calculate_gross_vs_net_returns(investor):
        """So sánh returns trước và sau phí"""
```

#### Tranche Manager
```python
class TrancheManager:
    """Quản lý các tranches của nhà đầu tư"""
    
    def create_tranche(investor_id, entry_date, nav, invested_amount):
        """Tạo tranche mới khi nạp tiền"""
    
    def split_tranche(tranche, withdrawal_amount):
        """Split tranche khi rút một phần"""
    
    def merge_tranches(tranches_list):
        """Merge tranches cùng điều kiện"""
    
    def update_tranche_units(tranche, nav_change):
        """Cập nhật units khi NAV thay đổi"""
```

## Data Components

### 1. Data Models

#### Domain Models Structure
```python
# models.py

@dataclass
class Investor:
    """Nhà đầu tư"""
    id: int
    name: str
    phone: str = ""
    address: str = ""
    email: str = ""
    join_date: date = None
    is_fund_manager: bool = False

@dataclass
class Tranche:
    """Lô giao dịch của nhà đầu tư"""
    investor_id: int
    tranche_id: str
    entry_date: datetime
    entry_nav: float
    units: float
    original_invested_value: float
    hwm: float = None
    original_entry_date: datetime = None
    original_entry_nav: float = None
    cumulative_fees_paid: float = 0.0

@dataclass
class Transaction:
    """Giao dịch nạp/rút tiền"""
    id: int
    investor_id: int
    transaction_type: str  # "deposit" or "withdrawal"
    amount: float
    transaction_date: datetime
    nav_after_transaction: float
    units_change: float
    price_per_unit: float
    notes: str = ""

@dataclass
class FeeRecord:
    """Bản ghi phí đã thu"""
    id: int
    investor_id: int
    fee_period: str
    fee_amount: float
    units_transferred: float
    calculated_date: datetime
    nav_at_calculation: float
    performance_percentage: float = None
```

### 2. Data Handlers

#### Supabase Data Handler
```python
class SupabaseDataHandler:
    """Primary database operations với PostgreSQL"""
    
    def __init__():
        """Khởi tạo connection với Supabase"""
    
    # CRUD operations
    def load_investors() -> List[Investor]:
    def save_investors(investors) -> bool:
    def load_tranches() -> List[Tranche]:
    def save_tranches(tranches) -> bool:
    def load_transactions() -> List[Transaction]:
    def save_transactions(transactions) -> bool:
    def load_fee_records() -> List[FeeRecord]:
    def save_fee_records(fee_records) -> bool:
    
    # Batch operations
    def save_all_data_enhanced(investors, tranches, transactions, fee_records):
        """Save tất cả data trong một transaction"""
    
    # Utility methods
    def test_connection() -> bool:
    def create_tables():
    def backup_database():
```

#### Enhanced Data Handler (CSV Fallback)
```python
class EnhancedDataHandler:
    """Fallback CSV storage khi database không available"""
    
    def __init__(backup_dir="backups"):
        """Initialize với backup directory"""
    
    # File operations
    def load_from_csv(filename) -> List:
    def save_to_csv(data, filename) -> bool:
    
    # Same interface như SupabaseDataHandler
    def load_investors() -> List[Investor]:
    def save_investors(investors) -> bool:
    # ... other methods
```

#### Database Save Optimization
```python
class DatabaseSaveOptimization:
    """Performance optimization cho database operations"""
    
    def batch_insert(table_name, records):
        """Batch insert để tăng performance"""
    
    def batch_update(table_name, updates):
        """Batch update operations"""
    
    def optimize_queries():
        """Query optimization strategies"""
```

### 3. External Services

#### Google Drive Manager
```python
class GoogleDriveManager:
    """Quản lý upload/download files từ Google Drive"""
    
    def __init__(credentials_json):
        """Initialize với service account credentials"""
    
    def upload_file(file_path, drive_folder_id):
        """Upload file lên Google Drive"""
    
    def create_folder(folder_name, parent_folder_id):
        """Tạo folder mới"""
    
    def download_file(file_id, local_path):
        """Download file từ Drive"""
    
    def list_files(folder_id):
        """List files trong folder"""
```

#### Realtime Sync Fix
```python
class RealtimeSyncFix:
    """Đồng bộ dữ liệu real-time"""
    
    def sync_with_database():
        """Sync local data với database"""
    
    def handle_concurrent_updates():
        """Xử lý concurrent data updates"""
    
    def resolve_conflicts():
        """Giải quyết data conflicts"""
```

#### File Manager
```python
class FileManager:
    """Quản lý local files và backups"""
    
    def create_backup(backup_name):
        """Tạo backup file"""
    
    def restore_from_backup(backup_file):
        """Restore từ backup"""
    
    def cleanup_old_backups():
        """Dọn dẹp backup files cũ"""
    
    def export_excel_report(data, filename):
        """Export data sang Excel"""
```

## Component Interactions

### 1. Data Flow Between Components
```
User Input → Page Component → Fund Manager → Data Handler → Database
         ← UI Update     ← Business Logic ← Data Response ←
```

### 2. Service Dependencies
```
Pages → Fund Manager → Data Handler → Database
      → Security Manager → Audit Logger
      → Utilities → Validation
```

### 3. Error Handling Chain
```
Database Error → Data Handler → Fund Manager → Page Component → User Notification
```

### 4. Caching Strategy
```
Database Data → Data Handler Cache → Fund Manager Cache → UI Cache → User Display
```