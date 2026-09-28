from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET_KEY = "dev-only-change-me-in-production-0123456789abcdef"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Local Disaster Preparedness System"
    api_prefix: str = "/api"
    debug: bool = False

    # sqlite by default for dev; set DATABASE_URL to a PostgreSQL DSN in production
    database_url: str = "sqlite:///./disaster_prep.db"

    secret_key: str = _DEV_SECRET_KEY
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8

    cors_origins: list[str] = ["*"]

    days_water_per_person: float = 3.0  # gallons
    rice_sacks_per_person: float = 0.1
    avg_persons_per_household: int = 4

    @model_validator(mode="after")
    def _reject_dev_secrets_in_production(self) -> "Settings":
        """Refuse to boot with the shared dev secret once Postgres is in play.

        The dev default is intentionally committed so a fresh clone runs with no
        setup, but shipping it would let anyone mint valid admin tokens.
        """
        if self.secret_key == _DEV_SECRET_KEY and not self.database_url.startswith("sqlite"):
            raise ValueError(
                "SECRET_KEY is still the committed development default while "
                "DATABASE_URL points at a non-SQLite database. Set a unique "
                "SECRET_KEY (>= 32 random bytes) before deploying."
            )
        return self

    @model_validator(mode="after")
    def _reject_credentials_with_wildcard_cors(self) -> "Settings":
        """`*` + credentials is rejected by browsers and unsafe if narrowed wrongly."""
        if "*" in self.cors_origins and len(self.cors_origins) > 1:
            raise ValueError(
                "CORS_ORIGINS cannot combine '*' with explicit origins. List the "
                "origins explicitly, e.g. CORS_ORIGINS='[\"https://drrm.gov.ph\"]'."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()