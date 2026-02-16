# API Documentation - Core Services

## EnhancedFundManager Service

Core business logic service cho Fund Management System.

### Class Overview

```python
class EnhancedFundManager:
    """
    Enhanced Fund Manager - Core business logic engine
    
    Attributes:
        data_handler: Database connection handler
        investors: List[Investor] - Danh sách nhà đầu tư
        tranches: List[Tranche] - Danh sách các tranches
        transactions: List[Transaction] - Lịch sử giao dịch
        fee_records: List[FeeRecord] - Lịch sử phí đã thu
    """
```

---

## Constructor & Initialization

### `__init__(self, data_handler)`

**Description**: Khởi tạo Fund Manager với data handler.

**Parameters**:
- `data_handler` (DataHandler): Instance của data handler

**Example**:
```python
from supabase_data_handler import SupabaseDataHandler
from services_enhanced import EnhancedFundManager

data_handler = SupabaseDataHandler()
fund_manager = EnhancedFundManager(data_handler)
```

---

## Data Management Methods

### `load_data(self) -> None`

**Description**: Load tất cả dữ liệu từ database sử dụng thread pool.

**Returns**: None

**Raises**: 
- `Exception`: Nếu không thể kết nối database

**Example**:
```python
fund_manager.load_data()
print(f"Loaded {len(fund_manager.investors)} investors")
```

### `save_data(self) -> bool`

**Description**: Lưu tất cả dữ liệu về database.

**Returns**: 
- `bool`: True nếu thành công, False nếu thất bại

**Example**:
```python
success = fund_manager.save_data()
if success:
    st.success("Đã lưu dữ liệu thành công")
else:
    st.error("Lỗi khi lưu dữ liệu")
```

---

## Investor Management Methods

### `add_investor(self, name: str, phone: str = "", address: str = "", email: str = "") -> Tuple[bool, str]`

**Description**: Thêm nhà đầu tư mới với validation.

**Parameters**:
- `name` (str): Tên nhà đầu tư (bắt buộc)
- `phone` (str, optional): Số điện thoại
- `address` (str, optional): Địa chỉ
- `email` (str, optional): Email

**Returns**: 
- `Tuple[bool, str]`: (success_status, message)

**Validation Rules**:
- Tên không được để trống
- Tên không được trùng (case-insensitive)
- Phone phải theo regex: `^(\+84|0)[0-9]{9,10}$`
- Email phải hợp lệ theo regex

**Example**:
```python
success, message = fund_manager.add_investor(
    name="Nguyễn Văn A",
    phone="0901234567", 
    email="nva@email.com"
)

if success:
    st.success(message)
else:
    st.error(message)
```

### `update_investor_info(self, updated_investors: List[Investor]) -> Tuple[bool, str]`

**Description**: Cập nhật thông tin multiple investors.

**Parameters**:
- `updated_investors` (List[Investor]): List investors đã update

**Returns**: 
- `Tuple[bool, str]`: (success_status, message)

**Example**:
```python
# Update thông tin investor
investor = fund_manager.get_investor_by_id(1)
investor.phone = "0987654321"

success, message = fund_manager.update_investor_info([investor])
```

### `get_investor_by_id(self, investor_id: int) -> Optional[Investor]`

**Description**: Lấy thông tin investor theo ID.

**Parameters**:
- `investor_id` (int): ID của investor

**Returns**: 
- `Optional[Investor]`: Investor object hoặc None

### `get_investor_options(self) -> Dict[str, int]`

**Description**: Lấy mapping tên -> ID để sử dụng trong selectbox.

**Returns**: 
- `Dict[str, int]`: {"Tên (ID: X)": investor_id}

**Example**:
```python
options = fund_manager.get_investor_options()
selected_name = st.selectbox("Chọn nhà đầu tư", options.keys())
selected_id = options[selected_name]
```

---

## Transaction Management Methods  

### `add_transaction(self, investor_id: int, transaction_type: str, amount: float, transaction_date: datetime, new_total_nav: float, notes: str = "") -> Tuple[bool, str]`

**Description**: Thêm giao dịch nạp/rút tiền với tranche management.

**Parameters**:
- `investor_id` (int): ID nhà đầu tư
- `transaction_type` (str): "deposit" hoặc "withdrawal"
- `amount` (float): Số tiền giao dịch (> 0)
- `transaction_date` (datetime): Ngày giao dịch
- `new_total_nav` (float): Total NAV mới sau giao dịch
- `notes` (str, optional): Ghi chú

**Returns**: 
- `Tuple[bool, str]`: (success_status, detailed_message)

**Business Logic**:
- **Deposit**: Tạo tranche mới với entry NAV và units tương ứng
- **Withdrawal**: Split tranches theo tỷ lệ, update units và values

**Example**:
```python
success, message = fund_manager.add_transaction(
    investor_id=1,
    transaction_type="deposit",
    amount=10000000,  # 10M VND
    transaction_date=datetime.now(),
    new_total_nav=550000000,  # 550M VND
    notes="Nạp tiền định kỳ"
)
```

### `fund_manager_withdrawal(self, amount: float, withdrawal_type: str) -> Tuple[bool, str]`

**Description**: Xử lý rút tiền cho Fund Manager từ units đã tích lũy.

**Parameters**:
- `amount` (float): Số tiền rút (nếu partial)
- `withdrawal_type` (str): "partial" hoặc "full"

**Returns**: 
- `Tuple[bool, str]`: (success_status, message_with_details)

**Business Logic**:
- Chỉ Fund Manager (ID=0) mới có thể rút
- Rút từ units đã nhận từ phí hiệu suất
- Tự động tính units cần trừ dựa trên current NAV

**Example**:
```python
success, message = fund_manager.fund_manager_withdrawal(
    amount=5000000,  # 5M VND
    withdrawal_type="partial"
)
```

---

## Fee Calculation Methods

### `calculate_fees_preview(self, year: str, end_date: date, final_nav: float) -> Tuple[bool, str, Dict]`

**Description**: Tính toán preview phí hiệu suất trước khi apply.

**Parameters**:
- `year` (str): Năm tính phí (e.g., "2024")
- `end_date` (date): Ngày kết thúc kỳ tính phí  
- `final_nav` (float): Total NAV cuối kỳ

**Returns**: 
- `Tuple[bool, str, Dict]`: (success, message, preview_data)

**Preview Data Structure**:
```python
{
    "fee_summary": [
        {
            "investor_name": str,
            "investor_id": int,
            "fee_amount": float,
            "units_to_transfer": float,
            "remaining_units": float,
            "performance_pct": float
        }
    ],
    "fee_details": [...],  # Chi tiết từng tranche
    "totals": {
        "total_fees": float,
        "total_units_transfer": float
    }
}
```

**Example**:
```python
success, message, preview = fund_manager.calculate_fees_preview(
    year="2024",
    end_date=date(2024, 12, 31),
    final_nav=600000000
)

if success:
    st.write(f"Tổng phí: {preview['totals']['total_fees']:,.0f} VND")
```

### `apply_fees(self, year: str, end_date: date, final_nav: float) -> Tuple[bool, str]`

**Description**: Áp dụng phí hiệu suất - **KHÔNG THỂ HOÀN TÁC**.

**Parameters**: Giống `calculate_fees_preview`

**Returns**: 
- `Tuple[bool, str]`: (success_status, message)

**Side Effects**:
- Trừ units từ investor tranches
- Cộng units vào Fund Manager
- Tạo fee_records
- Update High Water Marks
- Update cumulative_fees_paid

**Example**:
```python
# Sau khi đã review preview
success, message = fund_manager.apply_fees(
    year="2024", 
    end_date=date(2024, 12, 31),
    final_nav=600000000
)

if success:
    st.success("✅ Đã áp dụng phí thành công!")
    st.balloons()
```

### `calculate_individual_fee(self, investor_id: int, calc_date: date, current_nav: float) -> Tuple[bool, str, Dict]`

**Description**: Tính phí tạm thời cho một nhà đầu tư cụ thể.

**Parameters**:
- `investor_id` (int): ID nhà đầu tư
- `calc_date` (date): Ngày tính phí
- `current_nav` (float): NAV hiện tại

**Returns**: 
- `Tuple[bool, str, Dict]`: (success, message, calculation_details)

**Usage**: Để preview phí trước khi investor rút tiền.

---

## Statistics & Reporting Methods

### `get_investor_statistics(self, total_nav: float) -> List[Dict]`

**Description**: Tính toán thống kê chi tiết cho tất cả investors.

**Parameters**:
- `total_nav` (float): Total NAV hiện tại để tính giá trị

**Returns**: 
- `List[Dict]`: Stats cho từng investor

**Statistics Structure**:
```python
{
    "investor_id": int,
    "name": str,
    "total_invested": float,  # Tổng tiền đã nạp
    "total_withdrawn": float,  # Tổng tiền đã rút
    "net_invested": float,    # = invested - withdrawn
    "current_units": float,   # Số units hiện tại
    "current_value": float,   # Giá trị hiện tại (units * price_per_unit)
    "gain_loss": float,      # Lãi/lỗ = current_value - net_invested
    "gain_loss_pct": float,  # % lãi/lỗ
    "total_fees_paid": float, # Tổng phí đã trả
    "entry_dates": List[date], # Các ngày entry
    "join_date": date
}
```

### `calculate_lifetime_performance(self, total_nav: float) -> List[Dict]`

**Description**: Tính lifetime performance chi tiết cho reporting.

**Parameters**:
- `total_nav` (float): Total NAV để tính current values

**Returns**: 
- `List[Dict]`: Lifetime performance data

**Performance Data**:
```python
{
    "investor_name": str,
    "investor_id": int,
    "total_invested": float,
    "total_withdrawn": float, 
    "net_capital": float,
    "current_value": float,
    "gross_gain_loss": float,      # Trước phí
    "total_fees_paid": float,
    "net_gain_loss": float,        # Sau phí  
    "gross_return_pct": float,
    "net_return_pct": float,
    "fee_impact_pct": float        # Impact của phí lên return
}
```

---

## Utility Methods

### `get_fund_manager(self) -> Optional[Investor]`

**Description**: Lấy Fund Manager investor.

### `get_regular_investors(self) -> List[Investor]`

**Description**: Lấy danh sách investors thường (không phải Fund Manager).

### `_ensure_fund_manager_exists(self)`

**Description**: Đảm bảo Fund Manager tồn tại, tạo mới nếu chưa có.

### `_calculate_price_per_unit(self, total_nav: float) -> float`

**Description**: Tính giá mỗi unit dựa trên total NAV.

**Formula**: `price_per_unit = total_nav / total_units_outstanding`

---

## Error Handling

### Common Exception Types

```python
class FundManagerError(Exception):
    """Base exception for Fund Manager operations"""

class InvestorNotFoundError(FundManagerError):
    """Raised when investor ID not found"""

class InsufficientUnitsError(FundManagerError):
    """Raised when trying to withdraw more than available"""

class ValidationError(FundManagerError):
    """Raised for validation failures"""
```

### Error Response Format

All methods return tuple format: `(bool, str)` hoặc `(bool, str, data)`

- `True, "Success message"` - Operation thành công
- `False, "Error message"` - Operation thất bại với lý do

---

## Usage Examples

### Complete Transaction Flow

```python
# 1. Initialize
data_handler = SupabaseDataHandler()
fm = EnhancedFundManager(data_handler)
fm.load_data()

# 2. Add investor
success, msg = fm.add_investor("Nguyễn Văn A", "0901234567")

# 3. Add deposit transaction  
success, msg = fm.add_transaction(
    investor_id=1,
    transaction_type="deposit", 
    amount=100000000,  # 100M
    transaction_date=datetime.now(),
    new_total_nav=500000000  # 500M
)

# 4. Calculate fees preview
success, msg, preview = fm.calculate_fees_preview(
    year="2024",
    end_date=date(2024, 12, 31), 
    final_nav=600000000
)

# 5. Apply fees if confirmed
if user_confirmed:
    success, msg = fm.apply_fees("2024", date(2024, 12, 31), 600000000)

# 6. Save data
fm.save_data()
```

### Report Generation

```python
# Get comprehensive statistics
stats = fm.get_investor_statistics(total_nav=600000000)
performance = fm.calculate_lifetime_performance(total_nav=600000000)

# Create report
report_data = {
    "statistics": stats,
    "performance": performance,
    "summary": {
        "total_nav": 600000000,
        "total_investors": len(fm.get_regular_investors()),
        "total_fees_collected": sum(record.fee_amount for record in fm.fee_records)
    }
}
```