from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


UserRole = Literal["viewer", "admin", "fund_manager"]


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserInfo(BaseModel):
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime

