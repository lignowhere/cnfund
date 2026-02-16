from datetime import date, datetime

from pydantic import BaseModel

from .fees import FeeRecordDTO
from .transactions import TransactionDTO


class DashboardKPIDTO(BaseModel):
    total_nav: float
    total_investors: int
    total_units: float
    total_fees_paid: float
    fund_manager_value: float
    gross_return: float


class TopInvestorDTO(BaseModel):
    investor_id: int
    investor_name: str
    balance: float
    profit: float
    profit_percent: float


class DashboardResponseDTO(BaseModel):
    kpis: DashboardKPIDTO
    top_investors: list[TopInvestorDTO]


class InvestorProfileDTO(BaseModel):
    id: int
    name: str
    phone: str = ""
    email: str = ""
    address: str = ""
    province_code: str = ""
    province_name: str = ""
    ward_code: str = ""
    ward_name: str = ""
    address_line: str = ""
    join_date: date


class InvestorLifetimeDTO(BaseModel):
    original_invested: float
    current_value: float
    total_fees_paid: float
    gross_profit: float
    net_profit: float
    gross_return: float
    net_return: float
    current_units: float


class InvestorFeeDetailsDTO(BaseModel):
    total_fee: float
    balance: float
    invested_value: float
    profit: float
    profit_perc: float
    hurdle_value: float
    hwm_value: float
    excess_profit: float
    units_before: float
    units_after: float


class InvestorTrancheDTO(BaseModel):
    tranche_id: str
    entry_date: datetime
    entry_nav: float
    units: float
    hwm: float
    invested_value: float
    original_invested_value: float
    cumulative_fees_paid: float


class InvestorReportDTO(BaseModel):
    investor: InvestorProfileDTO
    current_balance: float
    current_profit: float
    current_profit_perc: float
    lifetime_performance: InvestorLifetimeDTO
    fee_details: InvestorFeeDetailsDTO
    tranches: list[InvestorTrancheDTO]
    transactions: list[TransactionDTO]
    fee_history: list[FeeRecordDTO]
    report_date: datetime
    current_nav: float
    current_price: float


class TransactionReportSummaryDTO(BaseModel):
    total_count: int
    total_volume: float
    net_cash_flow: float
    by_type: dict[str, int]
    earliest_date: str | None = None
    latest_date: str | None = None


class TransactionReportDTO(BaseModel):
    summary: TransactionReportSummaryDTO
    items: list[TransactionDTO]
    total: int
    page: int
    page_size: int
