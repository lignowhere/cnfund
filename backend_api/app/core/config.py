from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CNFund API"
    environment: str = "development"
    api_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./backend_api.db"
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    admin_username: str = "admin"
    admin_password: str = "1997"
    admin_role: str = "admin"

    cnfund_data_source: str = "postgres"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    allowed_origin_regex: str = r"https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    feature_table_view: bool = True
    feature_backup_restore: bool = True
    feature_fee_safety: bool = True
    feature_transactions_load_more: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="API_",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
