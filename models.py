# models.py - Enhanced Data models
# =============================================================================

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List
import pandas as pd

@dataclass
class Investor:
    id: int
    name: str
    phone: str = ""
    address: str = ""
    email: str = ""
    join_date: date = field(default_factory=date.today)
    is_fund_manager: bool = False  # NEW: Đánh dấu fund manager
    
    def __post_init__(self):
        if isinstance(self.join_date, str):
            self.join_date = pd.to_datetime(self.join_date).date()
    
    @property
    def display_name(self) -> str:
        prefix = "🏛️ " if self.is_fund_manager else ""
        return f"{prefix}{self.id} - {self.name}"

@dataclass
class Tranche:
    investor_id: int
    tranche_id: str
    entry_date: datetime
    entry_nav: float
    units: float
    hwm: float
    # NEW FIELDS for preserving history
    original_entry_date: datetime = None
    original_entry_nav: float = None
    cumulative_fees_paid: float = 0.0
    
    def __post_init__(self):
        if isinstance(self.entry_date, str):
            self.entry_date = pd.to_datetime(self.entry_date)
        
        # Set original values if not provided (for backward compatibility)
        if self.original_entry_date is None:
            self.original_entry_date = self.entry_date
        if self.original_entry_nav is None:
            self.original_entry_nav = self.entry_nav
    
    @property
    def invested_value(self) -> float:
        """Current invested value (after any adjustments)"""
        return self.entry_nav * self.units
    
    @property
    def original_invested_value(self) -> float:
        """Original invested value (from first entry)"""
        return self.original_entry_nav * self.units

@dataclass
class Transaction:
    id: int
    investor_id: int
    date: datetime
    type: str
    amount: float
    nav: float
    units_change: float
    
    def __post_init__(self):
        if isinstance(self.date, str):
            self.date = pd.to_datetime(self.date)

@dataclass
class FeeRecord:
    """NEW: Record để track fee history chi tiết"""
    id: int
    period: str  # "2024", "2025", etc.
    investor_id: int
    fee_amount: float
    fee_units: float
    calculation_date: datetime
    units_before: float
    units_after: float
    nav_per_unit: float
    description: str = ""  # Optional description
    
    def __post_init__(self):
        if isinstance(self.calculation_date, str):
            self.calculation_date = pd.to_datetime(self.calculation_date)