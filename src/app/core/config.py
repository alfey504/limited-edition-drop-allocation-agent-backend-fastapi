from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    sneaker_api_base_url: str
    sneaker_api_key: str

    forecasting_api_base_url: str
    forecasting_api_key: str
    db_conn: str

    reports_dir: str = "reports"

    jwt_secret: str
    jwt_expire_minutes: int = 60 * 24

    gemini_api_key: str
    gemini_model: str = "gemini-3.1-flash-lite"


@lru_cache
def get_settings() -> Settings:
    return Settings()
