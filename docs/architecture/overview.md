# Tổng Quan Kiến Trúc Hệ Thống

## Kiến Trúc Tổng Thể

Hệ Thống Quản Lý Quỹ được xây dựng theo kiến trúc **Layered Architecture** với **MVC Pattern**, tối ưu hóa cho performance và maintainability.

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Streamlit UI   │  │     Pages       │  │    Styles    │ │
│  │     (app.py)     │  │  (pages/*.py)   │  │  (styles.py) │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ EnhancedFund    │  │  Security       │  │   Utils &    │ │
│  │ Manager         │  │  Manager        │  │ Validation   │ │
│  │(services_*.py)  │  │(security_*.py)  │  │ (utils.py)   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Data Models   │  │ Data Handlers   │  │   External   │ │
│  │   (models.py)   │  │  (supabase_*,   │  │   Services   │ │
│  │                 │  │  data_*.py)     │  │(google_drive)│ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   PostgreSQL    │  │  Google Drive   │  │   File       │ │
│  │   (Supabase)    │  │     API         │  │   System     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Presentation Layer

#### **app.py** - Main Application Entry Point
- Streamlit application bootstrapper
- Lazy loading và caching strategies
- Global configuration management
- Error handling và fallback mechanisms

#### **Pages Module** (pages/*.py)
- **investor_page.py**: Quản lý nhà đầu tư
- **transaction_page.py**: Quản lý giao dịch  
- **fee_page_enhanced.py**: Tính toán phí
- **report_page_enhanced.py**: Báo cáo và thống kê

#### **Styles System** (styles.py)
- Custom CSS styling
- Mobile-responsive design
- Theme management
- UI component styling

### 2. Business Logic Layer

#### **EnhancedFundManager** (services_enhanced.py)
Core business logic engine bao gồm:

```python
class EnhancedFundManager:
    # Core CRUD operations
    - add_investor()
    - update_investor()  
    - add_transaction()
    - calculate_fees()
    
    # Business rules
    - validate_transaction()
    - apply_fee_calculation()
    - manage_tranches()
    
    # Performance calculations
    - calculate_lifetime_performance()
    - get_investor_statistics()
```

#### **Security Manager** (security_manager.py)
- Authentication và authorization
- Session management
- Audit logging
- Data encryption

#### **Utilities** (utils.py, data_utils.py)
- Data validation helpers
- Number formatting
- Date/time utilities
- Email/phone validation

### 3. Data Layer

#### **Data Models** (models.py)
Domain models sử dụng Python dataclasses:

```python
@dataclass
class Investor:
    id: int
    name: str
    phone: str = ""
    address: str = ""
    email: str = ""
    join_date: date = None
    is_fund_manager: bool = False

@dataclass  
class Tranche:
    investor_id: int
    tranche_id: str
    entry_date: datetime
    entry_nav: float
    units: float
    original_invested_value: float
    hwm: float = None
    cumulative_fees_paid: float = 0.0

@dataclass
class Transaction:
    # Transaction details...

@dataclass
class FeeRecord:
    # Fee calculation records...
```

#### **Data Handlers**
- **SupabaseDataHandler**: Primary database operations
- **EnhancedDataHandler**: CSV fallback operations  
- **DatabaseSaveOptimization**: Performance optimizations

#### **External Services**
- **GoogleDriveManager**: File upload/download
- **RealtimeSyncFix**: Real-time data synchronization

### 4. Infrastructure Layer

#### **PostgreSQL Database** (via Supabase)
- Primary data storage
- ACID transactions
- Connection pooling
- SSL encryption

#### **Google Drive API**
- Report storage
- Backup management
- File sharing

#### **File System**
- Local data caching
- Temporary file management
- Backup storage

## Data Flow Architecture

### 1. User Request Flow

```
User Interaction → Streamlit UI → Page Component → Business Logic → Data Handler → Database
```

### 2. Transaction Processing Flow

```
Transaction Input → Validation → Fund Manager Service → Tranche Management → Database Update → UI Refresh
```

### 3. Fee Calculation Flow

```
Fee Request → Performance Calculation → HWM Validation → Fee Application → Unit Transfer → Record Creation
```

## Design Patterns

### 1. **Repository Pattern**
Data handlers act as repositories với abstract interfaces:

```python
class DataHandler:
    def load_investors() -> List[Investor]
    def save_investors(investors: List[Investor]) -> bool
    def load_transactions() -> List[Transaction]
    # ...
```

### 2. **Service Layer Pattern** 
Business logic được encapsulate trong services:

```python
class EnhancedFundManager:
    def __init__(self, data_handler):
        self.data_handler = data_handler
        
    def process_transaction(self, ...):
        # Business logic here
```

### 3. **Factory Pattern**
Tạo objects thông qua factories:

```python
@st.cache_resource
def load_fund_manager_class():
    try:
        from services_enhanced import EnhancedFundManager
        return EnhancedFundManager
    except Exception:
        from services import FundManager  # Fallback
        return FundManager
```

### 4. **Observer Pattern**
UI updates theo dõi data changes thông qua Streamlit's reactive model.

## Security Architecture

### 1. Authentication Layer
- Password-based admin authentication
- Session timeout management
- Login attempt limiting

### 2. Authorization Layer  
- Role-based access (Viewer vs Admin)
- Function-level permissions
- Data access controls

### 3. Data Security
- Database connection encryption (SSL)
- Sensitive data handling
- Audit trail logging

### 4. Input Validation
- Server-side validation
- SQL injection prevention
- Data type validation

## Performance Architecture

### 1. **Caching Strategy**
```python
# Resource caching
@st.cache_resource
def load_data_handler():
    return SupabaseDataHandler()

# Data caching với TTL
@st.cache_data(ttl=300)
def get_investor_stats(nav_value):
    return fm.get_investor_statistics(nav_value)
```

### 2. **Database Optimization**
- Connection pooling
- Query optimization
- Index strategies
- Lazy loading

### 3. **UI Performance**
- Component lazy loading
- Progressive loading
- Minimal re-renders
- Efficient state management

## Scalability Considerations

### 1. **Horizontal Scaling**
- Stateless application design
- Database connection pooling
- External service isolation

### 2. **Vertical Scaling**
- Memory-efficient data structures
- Optimized algorithms
- Resource caching

### 3. **Data Scaling**
- Pagination for large datasets
- Archive strategies
- Performance monitoring

## Deployment Architecture

### 1. **Development**
- Local Streamlit server
- Local PostgreSQL (optional)
- File-based fallback

### 2. **Staging**  
- Streamlit Cloud hosting
- Supabase PostgreSQL
- Google Drive integration

### 3. **Production**
- Container deployment (Docker)
- Cloud database (Supabase)
- CDN for static assets
- Monitoring và logging

## Integration Points

### 1. **Database Integration**
- SQLAlchemy ORM
- Connection pooling
- Transaction management
- Error handling

### 2. **External API Integration**
- Google Drive API
- Error handling và retries
- Rate limiting
- Authentication management

### 3. **File System Integration**
- Local file operations
- Backup management
- Export/import functionality

## Error Handling Strategy

### 1. **Graceful Degradation**
- Database fallback to CSV
- Service fallback mechanisms
- User-friendly error messages

### 2. **Error Recovery**
- Automatic retry logic
- Transaction rollback
- State restoration

### 3. **Monitoring**
- Error logging
- Performance metrics
- Health checks