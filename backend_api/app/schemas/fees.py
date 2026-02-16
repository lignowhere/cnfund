from datetime import date

from pydantic import BaseModel, Field


class FeePreviewRequest(BaseModel):
    end_date: date
    total_nav: float = Field(ge=0)


class FeeApplyRequest(BaseModel):
    year: int = Field(ge=2000, le=2100)
    end_date: date
    total_nav: float = Field(ge=0)
    confirm_token: str
    acknowledge_risk: bool = False
    acknowledge_backup: bool = False


class FeePreviewDTO(BaseModel):
    investor_id: int
    investor_name: str
    fee_amount: float
    fee_rate_percent: float
    units_to_transfer: float
    excess_profit: float


class FeePreviewSummaryDTO(BaseModel):
    total_fee_amount: float
    total_units_to_transfer: float
    investor_count: int


class FeePreviewBundleDTO(BaseModel):
    items: list[FeePreviewDTO]
    summary: FeePreviewSummaryDTO
    confirm_token: str
    generated_at: str


class FeeRecordDTO(BaseModel):
    id: int
    period: str
    investor_id: int
    fee_amount: float
    fee_units: float
    calculation_date: str
    description: str
