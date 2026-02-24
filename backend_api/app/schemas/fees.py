from datetime import date
from typing import Literal

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
    applied_performance_fee_rate: float
    applied_hurdle_rate: float
    fee_source: Literal["global", "override"]


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


class FeeGlobalConfigDTO(BaseModel):
    performance_fee_rate: float = Field(ge=0, le=1)
    hurdle_rate_annual: float = Field(ge=0, le=1)
    updated_at: str | None = None


class FeeGlobalConfigUpdateRequest(BaseModel):
    performance_fee_rate: float | None = Field(default=None, ge=0, le=1)
    hurdle_rate_annual: float | None = Field(default=None, ge=0, le=1)


class FeeInvestorOverrideDTO(BaseModel):
    investor_id: int = Field(ge=1)
    performance_fee_rate: float | None = Field(default=None, ge=0, le=1)
    hurdle_rate_annual: float | None = Field(default=None, ge=0, le=1)
    updated_at: str | None = None


class FeeInvestorOverrideUpsertRequest(BaseModel):
    performance_fee_rate: float | None = Field(default=None, ge=0, le=1)
    hurdle_rate_annual: float | None = Field(default=None, ge=0, le=1)


class FeeConfigBundleDTO(BaseModel):
    global_config: FeeGlobalConfigDTO
    overrides: list[FeeInvestorOverrideDTO]
