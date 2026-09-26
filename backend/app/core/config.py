from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Local Disaster Preparedness System"
    api_prefix: str = "/api"
    debug: bool = False

    # sqlite by default for dev; set DATABASE_URL to a PostgreSQL DSN in production
    database_url: str = "sqlite:///./disaster_prep.db"

    secret_key: str = "dev-only-change-me-in-production-0123456789abcdef"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8

    cors_origins: list[str] = ["*"]

    days_water_per_person: float = 3.0  # gallons
    rice_sacks_per_person: float = 0.1
    avg_persons_per_household: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()