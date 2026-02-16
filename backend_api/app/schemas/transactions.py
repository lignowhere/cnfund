from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class TransactionDTO(BaseModel):
    id: int
    investor_id: int
    investor_name: str
    date: datetime
    type: str
    amount: float
    nav: float
    units_change: float


class TransactionCardDTO(BaseModel):
    id: int
    investor_name: str
    type: str
    amount: float
    nav: float
    date: datetime
    units_change: float


class TransactionCreateRequest(BaseModel):
    transaction_type: Literal["deposit", "withdraw", "nav_update"]
    investor_id: int | None = None
    amount: float | None = Field(default=None, ge=0)
    total_nav: float = Field(ge=0)
    transaction_date: date

