from pydantic import BaseModel


class FeatureFlagsDTO(BaseModel):
    table_view: bool
    backup_restore: bool
    fee_safety: bool
    transactions_load_more: bool


class LocationProvinceDTO(BaseModel):
    code: str
    name: str


class LocationWardDTO(BaseModel):
    code: str
    name: str
    province_code: str
