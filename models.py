# models.py - Data models đơn giản
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
    
    def __post_init__(self):
        if isinstance(self.join_date, str):
            self.join_date = pd.to_datetime(self.join_date).date()
    
    @property
    def display_name(self) -> str:
        return f"{self.id} - {self.name}"

@dataclass
class Tranche:
    investor_id: int
    tranche_id: str
    entry_date: datetime
    entry_nav: float
    units: float
    hwm: float
    
    def __post_init__(self):
        if isinstance(self.entry_date, str):
            self.entry_date = pd.to_datetime(self.entry_date)
    
    @property
    def invested_value(self) -> float:
        return self.entry_nav * self.units

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
