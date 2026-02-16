from datetime import date

from pydantic import BaseModel, Field


class NavUpdateRequest(BaseModel):
    total_nav: float = Field(ge=0)
    transaction_date: date


class NavPointDTO(BaseModel):
    date: str
    nav: float
    type: str

