# API Documentation - Data Models

## Overview

Hệ thống sử dụng Python `dataclass` để define domain models với type hints và validation. Tất cả models được import từ `models.py`.

```python
from models import Investor, Tranche, Transaction, FeeRecord
```

---

## Investor Model

### Class Definition

```python
@dataclass
class Investor:
    """
    Nhà đầu tư - Core entity của hệ thống
    
    Represents both regular investors và Fund Manager
    """
    id: int
    name: str
    phone: str = ""
    address: str = ""
    email: str = ""
    join_date: date = None
    is_fund_manager: bool = False
```

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | `int` | ✅ | Unique identifier, 0 = Fund Manager |
| `name` | `str` | ✅ | Tên nhà đầu tư |
| `phone` | `str` | ❌ | Số điện thoại (format: +84/0xxxxxxxxx) |
| `address` | `str` | ❌ | Địa chỉ liên hệ |
| `email` | `str` | ❌ | Email liên hệ |
| `join_date` | `date` | ❌ | Ngày tham gia (default: today) |
| `is_fund_manager` | `bool` | ❌ | True nếu là Fund Manager (default: False) |

### Methods

#### `__post_init__(self)`
Tự động set `join_date = today()` nếu không được cung cấp.

#### `display_name -> str` (Property)
```python
@property
def display_name(self) -> str:
    """Tên hiển thị với ID"""
    return f"{self.name} (ID: {self.id})"
```

### Usage Examples

```python
# Tạo investor thường
investor = Investor(
    id=1,
    name="Nguyễn Văn A",
    phone="0901234567",
    email="nva@email.com"
)

# Tạo Fund Manager
fund_manager = Investor(
    id=0, 
    name="Fund Manager",
    is_fund_manager=True
)

# Sử dụng display_name
print(investor.display_name)  # "Nguyễn Văn A (ID: 1)"
```

### Validation Rules

- `id`: Phải unique, 0 reserved cho Fund Manager
- `name`: Không được empty, không được trùng lặp  
- `phone`: Nếu có thì phải match regex `^(\+84|0)[0-9]{9,10}$`
- `email`: Nếu có thì phải valid email format

---

## Tranche Model

### Class Definition

```python
@dataclass
class Tranche:
    """
    Lô giao dịch - Represents một lần nạp tiền của investor
    
    Mỗi lần investor nạp tiền sẽ tạo ra một tranche mới
    với entry date, entry NAV và units riêng biệt
    """
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
```

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `investor_id` | `int` | ✅ | Foreign key tới Investor |
| `tranche_id` | `str` | ✅ | Unique identifier (UUID format) |
| `entry_date` | `datetime` | ✅ | Ngày tạo tranche (có thể thay đổi do withdrawal) |
| `entry_nav` | `float` | ✅ | NAV khi entry (có thể thay đổi) |
| `units` | `float` | ✅ | Số units hiện tại |
| `original_invested_value` | `float` | ✅ | Số tiền gốc đã đầu tư |
| `hwm` | `float` | ❌ | High Water Mark cho fee calculation |
| `original_entry_date` | `datetime` | ❌ | Ngày entry gốc (không đổi) |
| `original_entry_nav` | `float` | ❌ | Entry NAV gốc (không đổi) |
| `cumulative_fees_paid` | `float` | ❌ | Tổng phí đã trả (default: 0.0) |

### Methods

#### `__post_init__(self)`
Tự động set các default values:
- `hwm = entry_nav` nếu chưa có
- `original_entry_date = entry_date` nếu chưa có
- `original_entry_nav = entry_nav` nếu chưa có

### Key Concepts

#### **High Water Mark (HWM)**
- Mốc performance cao nhất mà tranche đã đạt được
- Phí chỉ được tính trên performance vượt HWM
- Update khi performance mới > HWM hiện tại

#### **Original vs Current Values**
- `original_*`: Giá trị gốc không thay đổi, dùng để track lịch sử
- `entry_*`: Giá trị hiện tại, có thể thay đổi do withdrawal

### Usage Examples

```python
# Tạo tranche mới khi investor nạp tiền
tranche = Tranche(
    investor_id=1,
    tranche_id=str(uuid.uuid4()),
    entry_date=datetime.now(),
    entry_nav=1.0,  # Assuming NAV per unit
    units=1000.0,   # Calculated based on amount/nav
    original_invested_value=1000000.0  # 1M VND
)

# Tính current value của tranche
current_nav = 1.2  # NAV đã tăng 20%
current_value = tranche.units * current_nav

# Check performance vs HWM
current_performance = current_nav / tranche.entry_nav
if current_performance > tranche.hwm:
    excess_performance = current_performance - tranche.hwm
    # Có thể tính phí trên excess_performance
```

### Business Rules

1. **Tranche Creation**: Mỗi lần deposit tạo tranche mới
2. **Tranche Splitting**: Khi withdrawal < toàn bộ, split thành 2 tranches
3. **HWM Updates**: Chỉ increase, never decrease
4. **Fee Tracking**: `cumulative_fees_paid` accumulates over time

---

## Transaction Model

### Class Definition

```python
@dataclass
class Transaction:
    """
    Giao dịch nạp/rút tiền của nhà đầu tư
    
    Ghi lại mọi movement của tiền và units
    """
    id: int
    investor_id: int
    transaction_type: str
    amount: float
    transaction_date: datetime
    nav_after_transaction: float
    units_change: float
    price_per_unit: float
    notes: str = ""
```

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | `int` | ✅ | Auto-increment primary key |
| `investor_id` | `int` | ✅ | Foreign key tới Investor |
| `transaction_type` | `str` | ✅ | "deposit", "withdrawal", "fee_collection" |
| `amount` | `float` | ✅ | Số tiền giao dịch (always positive) |
| `transaction_date` | `datetime` | ✅ | Timestamp của giao dịch |
| `nav_after_transaction` | `float` | ✅ | Total NAV sau khi giao dịch |
| `units_change` | `float` | ✅ | Thay đổi units (+/-) |
| `price_per_unit` | `float` | ✅ | Giá mỗi unit tại thời điểm giao dịch |
| `notes` | `str` | ❌ | Ghi chú thêm |

### Transaction Types

| Type | Description | Units Change | Amount Sign |
|------|-------------|--------------|-------------|
| `"deposit"` | Nạp tiền | `+` | `+` |
| `"withdrawal"` | Rút tiền | `-` | `+` |
| `"fee_collection"` | Thu phí | `-` (investor), `+` (FM) | `+` |
| `"fund_manager_withdrawal"` | FM rút tiền | `-` | `+` |

### Usage Examples

```python
# Deposit transaction
deposit = Transaction(
    id=1,
    investor_id=1,
    transaction_type="deposit",
    amount=10000000.0,  # 10M VND
    transaction_date=datetime.now(),
    nav_after_transaction=510000000.0,  # Total NAV after
    units_change=+8333.33,  # Units được cấp
    price_per_unit=1200.0,  # 10M / 8333.33
    notes="Nạp tiền định kỳ Q3"
)

# Withdrawal transaction  
withdrawal = Transaction(
    id=2,
    investor_id=1,
    transaction_type="withdrawal", 
    amount=5000000.0,  # 5M VND
    transaction_date=datetime.now(),
    nav_after_transaction=505000000.0,
    units_change=-4166.67,  # Units bị trừ
    price_per_unit=1200.0,
    notes="Rút tiền cấp thiết"
)
```

### Business Rules

1. `amount` luôn positive, direction thể hiện qua `units_change`
2. `nav_after_transaction` phải reflect đúng total NAV sau giao dịch
3. `units_change` và `price_per_unit` phải consistent với `amount`
4. Transaction type phải match với units_change sign

---

## FeeRecord Model

### Class Definition

```python
@dataclass
class FeeRecord:
    """
    Bản ghi phí hiệu suất đã thu
    
    Lưu lại lịch sử tất cả các lần thu phí
    """
    id: int
    investor_id: int
    fee_period: str
    fee_amount: float
    units_transferred: float
    calculated_date: datetime
    nav_at_calculation: float
    performance_percentage: float = None
```

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | `int` | ✅ | Auto-increment primary key |
| `investor_id` | `int` | ✅ | Foreign key tới Investor |
| `fee_period` | `str` | ✅ | Kỳ tính phí (e.g., "2024") |
| `fee_amount` | `float` | ✅ | Số tiền phí (VND) |
| `units_transferred` | `float` | ✅ | Số units chuyển cho Fund Manager |
| `calculated_date` | `datetime` | ✅ | Ngày tính và áp dụng phí |
| `nav_at_calculation` | `float` | ✅ | Total NAV tại thời điểm tính phí |
| `performance_percentage` | `float` | ❌ | % performance trigger phí |

### Usage Examples

```python
# Fee record sau khi apply fees
fee_record = FeeRecord(
    id=1,
    investor_id=1,
    fee_period="2024",
    fee_amount=2000000.0,  # 2M VND phí
    units_transferred=1666.67,  # Units chuyển cho FM
    calculated_date=datetime.now(),
    nav_at_calculation=600000000.0,  # 600M total NAV
    performance_percentage=15.5  # 15.5% performance
)

# Query fees by period
fees_2024 = [fee for fee in fee_records if fee.fee_period == "2024"]
total_fees_2024 = sum(fee.fee_amount for fee in fees_2024)
```

### Business Rules

1. Fee chỉ được tạo khi có excess performance over HWM
2. `units_transferred` = `fee_amount / price_per_unit` tại thời điểm tính
3. Fee period format: "YYYY" hoặc "YYYY-QX"
4. Mỗi investor có thể có multiple fee records per period (từ different tranches)

---

## Model Relationships

### Database Schema Relationships

```
Investor (1) ──────── (N) Tranche
    │                     │
    │                     │
    │ (1)               (1) │
    │                     │
    └─── (N) Transaction  │
    │                     │
    └─── (N) FeeRecord ───┘
```

### Foreign Key Constraints

```sql
-- Tranches reference Investors
ALTER TABLE tranches 
ADD FOREIGN KEY (investor_id) REFERENCES investors(id);

-- Transactions reference Investors  
ALTER TABLE transactions
ADD FOREIGN KEY (investor_id) REFERENCES investors(id);

-- FeeRecords reference Investors
ALTER TABLE fee_records  
ADD FOREIGN KEY (investor_id) REFERENCES investors(id);
```

---

## Model Utilities

### Type Conversion Helpers

```python
# Convert from database row to model
def row_to_investor(row) -> Investor:
    return Investor(
        id=row['id'],
        name=row['name'],
        phone=row['phone'] or "",
        address=row['address'] or "",
        email=row['email'] or "", 
        join_date=row['join_date'],
        is_fund_manager=row['is_fund_manager']
    )

def investor_to_dict(investor: Investor) -> dict:
    return {
        'id': investor.id,
        'name': investor.name,
        'phone': investor.phone,
        'address': investor.address,
        'email': investor.email,
        'join_date': investor.join_date,
        'is_fund_manager': investor.is_fund_manager
    }
```

### Validation Helpers  

```python
def validate_investor(investor: Investor) -> List[str]:
    """Validate investor data, return list of errors"""
    errors = []
    
    if not investor.name.strip():
        errors.append("Tên không được để trống")
    
    if investor.phone and not validate_phone(investor.phone):
        errors.append("Số điện thoại không hợp lệ")
        
    if investor.email and not validate_email(investor.email):
        errors.append("Email không hợp lệ")
        
    return errors

def validate_tranche(tranche: Tranche) -> List[str]:
    """Validate tranche data"""
    errors = []
    
    if tranche.units <= 0:
        errors.append("Units phải > 0")
        
    if tranche.entry_nav <= 0:
        errors.append("Entry NAV phải > 0")
        
    if tranche.original_invested_value <= 0:
        errors.append("Invested value phải > 0")
        
    return errors
```

---

## Serialization

### JSON Serialization

```python
import json
from datetime import datetime, date

def model_to_json(obj):
    """Custom JSON encoder for models"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj)

# Usage
investor_json = json.dumps(investor, default=model_to_json, indent=2)
```

### DataFrame Conversion

```python
import pandas as pd

def investors_to_dataframe(investors: List[Investor]) -> pd.DataFrame:
    """Convert investors list to pandas DataFrame"""
    return pd.DataFrame([
        {
            'ID': inv.id,
            'Tên': inv.name,
            'SĐT': inv.phone,
            'Email': inv.email,
            'Ngày tham gia': inv.join_date,
            'Fund Manager': inv.is_fund_manager
        }
        for inv in investors
    ])

def tranches_to_dataframe(tranches: List[Tranche]) -> pd.DataFrame:
    """Convert tranches to DataFrame for analysis"""
    return pd.DataFrame([
        {
            'Investor ID': t.investor_id,
            'Tranche ID': t.tranche_id,
            'Entry Date': t.entry_date,
            'Entry NAV': t.entry_nav,
            'Units': t.units,
            'Original Value': t.original_invested_value,
            'HWM': t.hwm,
            'Fees Paid': t.cumulative_fees_paid
        }
        for t in tranches
    ])
```

---

## Model Extensions

### Computed Properties

```python
# Có thể extend models với computed properties
class InvestorExtended(Investor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tranches = []
        self._transactions = []
    
    @property
    def total_invested(self) -> float:
        """Tổng số tiền đã nạp"""
        return sum(t.amount for t in self._transactions 
                  if t.transaction_type == "deposit")
    
    @property  
    def current_units(self) -> float:
        """Tổng units hiện tại"""
        return sum(t.units for t in self._tranches)
    
    def current_value(self, nav_per_unit: float) -> float:
        """Giá trị hiện tại"""
        return self.current_units * nav_per_unit
```

### Business Logic Methods

```python
class TrancheExtended(Tranche):
    def calculate_performance(self, current_nav: float) -> float:
        """Tính performance hiện tại"""
        return (current_nav / self.entry_nav) - 1
    
    def calculate_current_value(self, current_nav: float) -> float:
        """Tính giá trị hiện tại của tranche"""
        return self.units * current_nav
    
    def is_profitable(self, current_nav: float) -> bool:
        """Check xem có lãi không"""
        return self.calculate_performance(current_nav) > 0
    
    def excess_performance_over_hwm(self, current_nav: float) -> float:
        """Tính excess performance để tính phí"""
        current_perf = current_nav / self.entry_nav
        return max(0, current_perf - self.hwm)
```