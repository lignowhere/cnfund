from datetime import datetime

from pydantic import BaseModel, Field


class InvestorAccountAdminDTO(BaseModel):
    investor_id: int
    investor_name: str
    has_account: bool
    username: str | None = None
    is_active: bool | None = None
    created_at: datetime | None = None


class InvestorAccountCreateRequest(BaseModel):
    investor_id: int = Field(ge=1)
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class InvestorAccountUpdateRequest(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=64)
    is_active: bool | None = None


class InvestorAccountResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=1, max_length=128)
