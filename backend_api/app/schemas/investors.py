from datetime import date

from pydantic import BaseModel, Field


class InvestorDTO(BaseModel):
    id: int
    name: str
    phone: str = ""
    address: str = ""
    email: str = ""
    join_date: date
    is_fund_manager: bool = False


class InvestorCardDTO(BaseModel):
    id: int
    display_name: str
    phone: str = ""
    email: str = ""
    current_value: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0


class InvestorCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = ""
    address: str = ""
    email: str = ""


class InvestorUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = None
    address: str | None = None
    email: str | None = None


class InvestorSummaryDTO(BaseModel):
    investor_id: int
    investor_name: str
    nav_used: float
    units: float
    balance: float
    profit: float
    profit_percent: float
    lifetime: dict

