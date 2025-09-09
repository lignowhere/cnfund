from datetime import date, datetime
from typing import Optional
from dataclasses import dataclass
from timezone_manager import TimezoneManager

@dataclass
class Investor:
    """Enhanced Investor model với is_fund_manager field"""
    id: int
    name: str
    phone: str = ""
    address: str = ""
    email: str = ""
    join_date: date = None
    is_fund_manager: bool = False
    
    def __post_init__(self):
        if self.join_date is None:
            self.join_date = date.today()
    
    @property
    def display_name(self) -> str:
        """Tên hiển thị với ID"""
        return f"{self.name} (ID: {self.id})"

@dataclass
class Tranche:
    """
    FIXED: Enhanced Tranche model với đầy đủ thuộc tính cần thiết
    """
    investor_id: int
    tranche_id: str
    entry_date: datetime
    entry_nav: float  # Giá NAV khi entry (có thể thay đổi do rút vốn)
    units: float

    # THAY ĐỔI QUAN TRỌNG: Biến nó thành một thuộc tính được lưu trữ, không phải @property
    original_invested_value: float 
    
    hwm: float = None  # High Water Mark
    original_entry_date: datetime = None  # Ngày entry gốc (không đổi)
    original_entry_nav: float = None  # NAV entry gốc (không đổi)
    cumulative_fees_paid: float = 0.0  # Tổng phí đã trả
    
    def __post_init__(self):
        # Set defaults if not provided
        if self.hwm is None:
            self.hwm = self.entry_nav
        if self.original_entry_date is None:
            self.original_entry_date = self.entry_date
        if self.original_entry_nav is None:
            self.original_entry_nav = self.entry_nav
        # 🔹 backing field để lưu cost basis hiện tại
        self._invested_value = self.units * self.entry_nav
    
    @property 
    def invested_value(self) -> float:
        """Vốn đầu tư hiện tại (có thể được cập nhật qua setter)."""
        return self._invested_value

    @invested_value.setter
    def invested_value(self, value: float):
        """Cho phép cập nhật cost basis khi có rút/fee."""
        self._invested_value = float(value)
    
    # @property
    # def days_held(self) -> int:
    #     """Số ngày đã hold"""
    #     return (datetime.now() - self.entry_date).days
    
    # @property
    # def years_held(self) -> float:
    #     """Số năm đã hold (dùng để tính hurdle)"""
    #     return self.days_held / 365.25
    
    def days_held(self, current_date: datetime) -> int:
        """Số ngày đã hold tính đến một ngày cụ thể."""
        return (current_date - self.entry_date).days

    def years_held(self, current_date: datetime) -> float:
        """Số năm đã hold tính đến một ngày cụ thể."""
        # Thêm kiểm tra để tránh số âm nếu current_date < entry_date
        days = self.days_held(current_date)
        return max(0, days / 365.25)
    
    def calculate_hurdle_price(self, current_date: datetime, hurdle_rate: float = 0.06) -> float:
        """Tính hurdle price dựa trên hurdle rate và một ngày cụ thể."""
        years = self.years_held(current_date)
        return self.entry_nav * ((1 + hurdle_rate) ** years)

    def get_performance_threshold(self, current_date: datetime, hurdle_rate: float = 0.06) -> float:
        """Lấy ngưỡng performance (max của hurdle và HWM) tại một ngày cụ thể."""
        hurdle_price = self.calculate_hurdle_price(current_date, hurdle_rate)
        return max(hurdle_price, self.hwm)

    def calculate_excess_profit(self, current_price: float, current_date: datetime, hurdle_rate: float = 0.06) -> float:
        """Tính lợi nhuận vượt ngưỡng cho tranche này tại một ngày cụ thể."""
        threshold = self.get_performance_threshold(current_date, hurdle_rate)
        if current_price > threshold:
            profit_per_unit = current_price - threshold
            return profit_per_unit * self.units
        return 0.0

    def calculate_performance_fee(self, current_price: float, current_date: datetime, fee_rate: float = 0.20, hurdle_rate: float = 0.06) -> float:
        """Tính performance fee cho tranche này tại một ngày cụ thể."""
        excess_profit = self.calculate_excess_profit(current_price, current_date, hurdle_rate)
        return excess_profit * fee_rate
    
    def update_hwm(self, new_price: float) -> None:
        """
        Cập nhật High Water Mark nếu giá mới cao hơn
        """
        if new_price > self.hwm:
            self.hwm = new_price
    
    def apply_fee(self, fee_amount: float, current_price: float) -> None:
        # chỉ ghi nhận phí, không đụng tới HWM
        self.cumulative_fees_paid += fee_amount
        # nếu muốn thì trừ units tại đây
        fee_units = fee_amount / current_price if current_price > 0 else 0
        self.units = max(0.0, self.units - fee_units)

@dataclass
class Transaction:
    """Transaction model (không thay đổi)"""
    id: int
    investor_id: int
    date: datetime
    type: str  # 'Nạp', 'Rút', 'NAV Update', 'Phí', 'Fund Manager Withdrawal'
    amount: float
    nav: float
    units_change: float

@dataclass
class FeeRecord:
    """Enhanced Fee Record model"""
    id: int
    period: str  # e.g., "2024", "Q1-2024"
    investor_id: int
    fee_amount: float
    fee_units: float
    calculation_date: datetime
    units_before: float
    units_after: float
    nav_per_unit: float
    description: str = ""
    
    @property
    def fee_date(self) -> datetime:
        """Alias cho calculation_date để backward compatibility"""
        return self.calculation_date
    
    @property
    def fee_percentage(self) -> float:
        """Tính tỷ lệ phí so với giá trị trước phí"""
        value_before = self.units_before * self.nav_per_unit
        if value_before > 0:
            return (self.fee_amount / value_before) * 100
        return 0.0

# === HELPER CLASSES ===

@dataclass
class PerformanceMetrics:
    """
    Class để tính toán các metrics performance
    """
    original_investment: float
    current_value: float
    fees_paid: float
    
    @property
    def gross_profit(self) -> float:
        """Lợi nhuận trước phí"""
        return self.current_value - self.original_investment
    
    @property
    def net_profit(self) -> float:
        """Lợi nhuận sau phí"""
        return self.gross_profit - self.fees_paid
    
    @property
    def gross_return(self) -> float:
        """Tỷ suất sinh lời trước phí"""
        if self.original_investment > 0:
            return self.gross_profit / self.original_investment
        return 0.0
    
    @property
    def net_return(self) -> float:
        """Tỷ suất sinh lời sau phí"""
        if self.original_investment > 0:
            return self.net_profit / self.original_investment
        return 0.0
    
    @property
    def fee_drag(self) -> float:
        """Ảnh hưởng của phí đến return"""
        return self.gross_return - self.net_return
    
    @property
    def fee_as_percentage_of_investment(self) -> float:
        """Phí như % của vốn đầu tư"""
        if self.original_investment > 0:
            return (self.fees_paid / self.original_investment) * 100
        return 0.0

@dataclass 
class FeeCalculationDetail:
    """
    Class để lưu chi tiết tính phí
    """
    investor_id: int
    investor_name: str
    total_units: float
    current_balance: float
    invested_value: float  # Current cost basis
    original_invested_value: float  # Original investment
    profit_vs_current: float
    profit_vs_original: float
    hurdle_value: float
    hwm_value: float
    excess_profit: float
    performance_fee: float
    units_to_transfer: float
    
    @property
    def fee_rate_vs_balance(self) -> float:
        """Fee rate so với balance hiện tại"""
        if self.current_balance > 0:
            return (self.performance_fee / self.current_balance) * 100
        return 0.0
    
    @property
    def fee_rate_vs_excess_profit(self) -> float:
        """Fee rate so với excess profit (should be 20%)"""
        if self.excess_profit > 0:
            return (self.performance_fee / self.excess_profit) * 100
        return 0.0

# === VALIDATION FUNCTIONS ===

def validate_tranche(tranche: Tranche) -> tuple[bool, list[str]]:
    """
    Validate tranche data
    Returns: (is_valid, list_of_errors)
    """
    errors = []
    
    if tranche.units <= 0:
        errors.append("Units phải lớn hơn 0")
    
    if tranche.entry_nav <= 0:
        errors.append("Entry NAV phải lớn hơn 0")
    
    if tranche.original_entry_nav <= 0:
        errors.append("Original entry NAV phải lớn hơn 0")
    
    if tranche.hwm < tranche.entry_nav:
        errors.append("HWM không thể nhỏ hơn entry NAV")
    
    if tranche.cumulative_fees_paid < 0:
        errors.append("Cumulative fees không thể âm")
    
    # Use timezone-aware comparison to avoid offset-naive vs offset-aware error
    current_time = TimezoneManager.now()
    entry_time = TimezoneManager.normalize_for_display(tranche.entry_date)
    
    if entry_time > current_time:
        errors.append("Entry date không thể ở tương lai")
    
    # Compare normalized dates for consistency
    original_entry_time = TimezoneManager.normalize_for_display(tranche.original_entry_date)
    if original_entry_time > entry_time:
        errors.append("Original entry date không thể sau entry date")
    
    return len(errors) == 0, errors

def validate_transaction(transaction: Transaction) -> tuple[bool, list[str]]:
    """
    Validate transaction data
    """
    errors = []
    
    # Use timezone-aware comparison to avoid offset-naive vs offset-aware error
    current_time = TimezoneManager.now()
    transaction_time = TimezoneManager.normalize_for_display(transaction.date)
    
    if transaction_time > current_time:
        errors.append("Transaction date không thể ở tương lai")
    
    # Validate based on transaction type
    if transaction.type in ['Nạp', 'Phí Nhận'] and transaction.amount <= 0:
        errors.append(f"Amount cho {transaction.type} phải dương")
    
    if transaction.type in ['Rút', 'Phí', 'Fund Manager Withdrawal'] and transaction.amount >= 0:
        errors.append(f"Amount cho {transaction.type} phải âm")
    
    if transaction.type != 'NAV Update' and transaction.nav <= 0:
        errors.append("NAV phải lớn hơn 0")
    
    return len(errors) == 0, errors

def validate_fee_record(fee_record: FeeRecord) -> tuple[bool, list[str]]:
    """
    Validate fee record data
    """
    errors = []
    
    if fee_record.fee_amount < 0:
        errors.append("Fee amount không thể âm")
    
    if fee_record.fee_units < 0:
        errors.append("Fee units không thể âm")
    
    if fee_record.units_after > fee_record.units_before:
        errors.append("Units after không thể lớn hơn units before")
    
    if fee_record.nav_per_unit <= 0:
        errors.append("NAV per unit phải lớn hơn 0")
    
    if fee_record.calculation_date > datetime.now():
        errors.append("Calculation date không thể ở tương lai")
    
    # Check consistency
    expected_units_after = fee_record.units_before - fee_record.fee_units
    if abs(fee_record.units_after - expected_units_after) > 0.000001:
        errors.append("Units calculation không nhất quán")
    
    expected_fee_amount = fee_record.fee_units * fee_record.nav_per_unit
    if abs(fee_record.fee_amount - expected_fee_amount) > 0.01:  # Allow 1 VND difference
        errors.append("Fee amount calculation không nhất quán")
    
    return len(errors) == 0, errors

# === UTILITY FUNCTIONS ===

def create_sample_tranche(investor_id: int, amount: float, nav_price: float, 
                         entry_date: datetime = None) -> Tranche:
    """
    Tạo sample tranche cho testing
    """
    if entry_date is None:
        entry_date = datetime.now()
    
    units = amount / nav_price
    
    return Tranche(
        investor_id=investor_id,
        tranche_id=f"TEST_{investor_id}_{int(entry_date.timestamp())}",
        entry_date=entry_date,
        entry_nav=nav_price,
        units=units,
        # THÊM DÒNG NÀY:
        original_invested_value=amount,
        hwm=nav_price,
        original_entry_date=entry_date,
        original_entry_nav=nav_price,
        cumulative_fees_paid=0.0
    )

def create_sample_investor(investor_id: int, name: str, is_fm: bool = False) -> Investor:
    """
    Tạo sample investor cho testing  
    """
    return Investor(
        id=investor_id,
        name=name,
        phone=f"098765432{investor_id}",
        address=f"Address {investor_id}",
        email=f"investor{investor_id}@example.com",
        join_date=date.today(),
        is_fund_manager=is_fm
    )

# === CONSTANTS FOR EASY REFERENCE ===

DEFAULT_HURDLE_RATE = 0.06  # 6% annual hurdle rate
DEFAULT_PERFORMANCE_FEE_RATE = 0.20  # 20% performance fee
DEFAULT_UNIT_PRICE = 10000.0  # Default unit price in VND

TRANSACTION_TYPES = [
    'Nạp',
    'Rút', 
    'NAV Update',
    'Phí',
    'Phí Nhận',
    'Fund Manager Withdrawal'
]

POSITIVE_AMOUNT_TYPES = ['Nạp', 'Phí Nhận']
NEGATIVE_AMOUNT_TYPES = ['Rút', 'Phí', 'Fund Manager Withdrawal']
ZERO_AMOUNT_TYPES = ['NAV Update']