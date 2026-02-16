# API Documentation - Database Handler

## SupabaseDataHandler

Primary database handler cho PostgreSQL database thông qua Supabase.

### Class Overview

```python
class SupabaseDataHandler:
    """
    Optimized Supabase PostgreSQL data handler với robust initialization
    
    Attributes:
        engine: SQLAlchemy engine instance
        connected: bool - Connection status
        connection_info: dict - Connection metadata
        version_info: dict - Database version info
    """
```

---

## Constructor & Connection Management

### `__init__(self)`

**Description**: Khởi tạo data handler với lazy connection.

**Process Flow**:
1. Initialize engine (không connect ngay)
2. Parse database URL từ secrets/env
3. Thực hiện lightweight connection check
4. Tạo tables nếu cần thiết

**Example**:
```python
data_handler = SupabaseDataHandler()
if data_handler.connected:
    print("✅ Database connected successfully")
else:
    print("❌ Database connection failed")
```

### `_init_engine(self)`

**Description**: Khởi tạo SQLAlchemy engine với connection pooling.

**Configuration**:
```python
self.engine = create_engine(
    db_url,
    pool_pre_ping=True,
    connect_args={
        "sslmode": "require",
        "connect_timeout": 5
    }
)
```

### `_connect(self) -> bool`

**Description**: Test database connection với lightweight query.

**Returns**: 
- `bool`: True nếu connection thành công

**Test Query**: `SELECT 1` - minimal overhead

---

## Table Management

### `_create_tables(self)`

**Description**: Tạo tất cả tables cần thiết nếu chưa tồn tại.

**Tables Created**:

#### Investors Table
```sql
CREATE TABLE IF NOT EXISTS investors (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    email VARCHAR(255),
    join_date DATE NOT NULL,
    is_fund_manager BOOLEAN DEFAULT FALSE
);
```

#### Tranches Table  
```sql
CREATE TABLE IF NOT EXISTS tranches (
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
```

#### Transactions Table
```sql
CREATE TABLE IF NOT EXISTS transactions (
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
```

#### Fee Records Table
```sql
CREATE TABLE IF NOT EXISTS fee_records (
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

---

## CRUD Operations - Investors

### `load_investors(self) -> List[Investor]`

**Description**: Load tất cả investors từ database.

**Returns**: 
- `List[Investor]`: Danh sách investors

**SQL Query**:
```sql
SELECT * FROM investors ORDER BY id
```

**Example**:
```python
investors = data_handler.load_investors()
print(f"Loaded {len(investors)} investors")
```

### `save_investors(self, investors: List[Investor]) -> bool`

**Description**: Lưu danh sách investors về database.

**Parameters**:
- `investors` (List[Investor]): Danh sách để lưu

**Returns**: 
- `bool`: True nếu thành công

**Process**:
1. Begin transaction
2. Delete existing investors
3. Bulk insert new investors
4. Commit hoặc rollback

**Example**:
```python
success = data_handler.save_investors(investors)
if not success:
    st.error("Failed to save investors")
```

---

## CRUD Operations - Tranches

### `load_tranches(self) -> List[Tranche]`

**Description**: Load tất cả tranches từ database.

**Returns**: 
- `List[Tranche]`: Danh sách tranches

**SQL Query**:
```sql
SELECT * FROM tranches ORDER BY investor_id, entry_date
```

### `save_tranches(self, tranches: List[Tranche]) -> bool`

**Description**: Lưu danh sách tranches về database.

**Business Logic**:
- Replace toàn bộ table với data mới
- Maintain foreign key integrity
- Handle decimal precision cho financial data

---

## CRUD Operations - Transactions

### `load_transactions(self) -> List[Transaction]`

**Description**: Load tất cả transactions từ database.

**Returns**: 
- `List[Transaction]`: Danh sách transactions theo thứ tự chronological

**SQL Query**:
```sql
SELECT * FROM transactions ORDER BY transaction_date DESC
```

### `save_transactions(self, transactions: List[Transaction]) -> bool`

**Description**: Lưu danh sách transactions về database.

**Auto-increment Handling**:
```python
# Handle auto-increment ID cho new transactions
next_id = 1
for transaction in transactions:
    if transaction.id is None:
        transaction.id = next_id
        next_id += 1
```

---

## CRUD Operations - Fee Records

### `load_fee_records(self) -> List[FeeRecord]`

**Description**: Load tất cả fee records từ database.

**Returns**: 
- `List[FeeRecord]`: Danh sách fee records

**SQL Query**:
```sql
SELECT * FROM fee_records ORDER BY calculated_date DESC
```

### `save_fee_records(self, fee_records: List[FeeRecord]) -> bool`

**Description**: Lưu danh sách fee records về database.

**Note**: Fee records thường chỉ được thêm, không edit/delete.

---

## Batch Operations

### `save_all_data_enhanced(self, investors, tranches, transactions, fee_records) -> bool`

**Description**: Lưu tất cả data trong một transaction duy nhất.

**Parameters**:
- `investors` (List[Investor])
- `tranches` (List[Tranche]) 
- `transactions` (List[Transaction])
- `fee_records` (List[FeeRecord])

**Returns**: 
- `bool`: True nếu tất cả operations thành công

**Transaction Flow**:
```python
def save_all_data_enhanced(self, investors, tranches, transactions, fee_records):
    try:
        with self.engine.begin() as conn:
            # Save investors first (parent table)
            self._save_investors_batch(conn, investors)
            
            # Save dependent tables
            self._save_tranches_batch(conn, tranches)
            self._save_transactions_batch(conn, transactions)
            self._save_fee_records_batch(conn, fee_records)
            
            # All operations committed together
            return True
    except Exception as e:
        # Automatic rollback on any error
        return False
```

**Benefits**:
- ACID compliance
- All-or-nothing persistence
- Better performance than individual saves
- Referential integrity maintained

---

## Utility Methods

### `test_connection(self) -> bool`

**Description**: Test database connectivity.

**Usage**: Health checks và debugging

### `get_connection_info(self) -> dict`

**Description**: Lấy thông tin connection để display.

**Returns**:
```python
{
    "host": "hostname",
    "port": 5432,
    "database": "database_name",
    "user": "username",
    "status": "connected"
}
```

### `_parse_db_url(self, db_url: str) -> dict`

**Description**: Parse DATABASE_URL thành components.

**Example**:
```python
# Input: "postgresql://user:pass@host:5432/dbname"
# Output: {"host": "host", "port": 5432, "database": "dbname", "user": "user"}
```

---

## Error Handling

### Connection Errors

```python
try:
    data_handler = SupabaseDataHandler()
except Exception as e:
    st.error(f"Database initialization failed: {e}")
    # Fallback to CSV handler
    from data_handler import EnhancedDataHandler
    data_handler = EnhancedDataHandler()
```

### Query Errors

```python
def load_investors(self):
    try:
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM investors"))
            return [self._row_to_investor(row) for row in result]
    except Exception as e:
        st.error(f"Failed to load investors: {e}")
        return []  # Return empty list to prevent app crash
```

### Transaction Rollback

```python
def save_all_data_enhanced(self, ...):
    try:
        with self.engine.begin() as conn:  # Auto-rollback on exception
            # All database operations
            pass
    except Exception as e:
        # Automatic rollback happened
        st.error(f"Failed to save data: {e}")
        return False
```

---

## Performance Optimizations

### Connection Pooling

```python
# Engine configuration cho optimal performance
create_engine(
    database_url,
    pool_size=10,           # Connections trong pool
    max_overflow=20,        # Additional connections khi cần
    pool_timeout=30,        # Timeout chờ connection
    pool_recycle=3600,      # Recycle connections mỗi 1h
    pool_pre_ping=True      # Validate connections trước dùng
)
```

### Bulk Operations

```python
def _save_investors_batch(self, conn, investors):
    """Bulk insert thay vì individual INSERTs"""
    
    # Prepare data
    investor_data = [
        {
            'id': inv.id,
            'name': inv.name,
            'phone': inv.phone,
            'address': inv.address,
            'email': inv.email,
            'join_date': inv.join_date,
            'is_fund_manager': inv.is_fund_manager
        }
        for inv in investors
    ]
    
    # Bulk insert - much faster than individual INSERTs
    conn.execute(
        text("INSERT INTO investors (id, name, phone, address, email, join_date, is_fund_manager) "
             "VALUES (:id, :name, :phone, :address, :email, :join_date, :is_fund_manager)"),
        investor_data
    )
```

### Query Optimization

```python
# Sử dụng indexes
def create_indexes(self):
    """Create indexes cho performance"""
    with self.engine.begin() as conn:
        # Index cho foreign keys
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tranches_investor_id ON tranches(investor_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transactions_investor_id ON transactions(investor_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fee_records_investor_id ON fee_records(investor_id)"))
        
        # Index cho date queries
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fee_records_date ON fee_records(calculated_date)"))
```

---

## Backup & Recovery

### Database Backup

```python
def backup_database(self, backup_file: str) -> bool:
    """Create database backup"""
    try:
        import subprocess
        db_url = os.getenv("DATABASE_URL")
        
        # Use pg_dump for PostgreSQL backup
        result = subprocess.run([
            "pg_dump", 
            db_url,
            "-f", backup_file
        ], capture_output=True, text=True)
        
        return result.returncode == 0
    except Exception as e:
        st.error(f"Backup failed: {e}")
        return False
```

### Data Export

```python
def export_to_csv(self, table_name: str, output_file: str) -> bool:
    """Export table to CSV for backup"""
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, self.engine)
        df.to_csv(output_file, index=False)
        return True
    except Exception as e:
        st.error(f"Export failed: {e}")
        return False
```

---

## Migration Support

### Schema Migrations

```python
def migrate_database(self, target_version: int) -> bool:
    """Run database migrations to target version"""
    current_version = self._get_schema_version()
    
    if current_version < target_version:
        for version in range(current_version + 1, target_version + 1):
            if not self._run_migration(version):
                return False
    
    return True

def _run_migration(self, version: int) -> bool:
    """Run specific migration"""
    migration_sql = self._get_migration_sql(version)
    
    try:
        with self.engine.begin() as conn:
            conn.execute(text(migration_sql))
            conn.execute(text(f"UPDATE schema_version SET version = {version}"))
        return True
    except Exception as e:
        st.error(f"Migration {version} failed: {e}")
        return False
```

---

## Alternative Data Handler

### EnhancedDataHandler (CSV Fallback)

Khi Supabase không available, hệ thống tự động fallback về CSV storage:

```python
class EnhancedDataHandler:
    """Fallback CSV data handler"""
    
    def __init__(self, backup_dir="backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.connected = True  # CSV luôn "connected"
    
    def load_investors(self) -> List[Investor]:
        """Load từ investors.csv"""
        csv_file = self.backup_dir / "investors.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file)
            return [self._row_to_investor(row) for _, row in df.iterrows()]
        return []
    
    def save_investors(self, investors: List[Investor]) -> bool:
        """Save to investors.csv"""
        try:
            df = pd.DataFrame([asdict(inv) for inv in investors])
            df.to_csv(self.backup_dir / "investors.csv", index=False)
            return True
        except Exception:
            return False
```

**Usage**:
```python
# Automatic fallback trong app.py
@st.cache_resource
def load_data_handler():
    try:
        data_handler = SupabaseDataHandler()
        if data_handler.connected:
            return data_handler
    except:
        pass
    
    # Fallback to CSV
    st.warning("📄 Using CSV storage (database unavailable)")
    return EnhancedDataHandler()
```