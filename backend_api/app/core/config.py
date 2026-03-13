import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

_KNOWN_BAD_SECRETS = {"change-this-in-production", "secret", ""}
_KNOWN_BAD_PASSWORDS = {"1997", "password", "admin", ""}


class Settings(BaseSettings):
    app_name: str = "CNFund API"
    environment: str = "development"
    api_prefix: str = "/api/v1"

    database_url: str = ""
    jwt_secret_key: str  # required — no default
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    admin_username: str  # required — no default
    admin_password: str  # required — no default
    admin_role: str = "admin"

    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    allowed_origin_regex: str = r"https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    feature_table_view: bool = True
    feature_backup_restore: bool = True
    feature_fee_safety: bool = True
    feature_transactions_load_more: bool = True
    auto_backup_on_new_transaction: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="API_",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.jwt_secret_key in _KNOWN_BAD_SECRETS:
        raise RuntimeError(
            "API_JWT_SECRET_KEY must be set to a strong, unique secret."
        )
    if s.admin_password in _KNOWN_BAD_PASSWORDS:
        logger.warning(
            "API_ADMIN_PASSWORD is weak. Use a strong password in production."
        )
    return s
