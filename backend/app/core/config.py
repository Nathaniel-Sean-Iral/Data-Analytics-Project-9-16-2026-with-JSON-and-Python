from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET_KEY = "dev-only-change-me-in-production-0123456789abcdef"

# Every default secret that has ever been committed to this repo, including the
# fallback in docker-compose.yml. Matching only the dev default left the compose
# path booting Postgres with a publicly-known signing key.
_KNOWN_PLACEHOLDER_SECRETS = frozenset(
    {
        _DEV_SECRET_KEY,
        "change-me-in-production-0123456789abcdef0123456789abcdef",
    }
)

_PLACEHOLDER_MARKERS = ("change-me", "changeme", "dev-only", "placeholder", "example", "your-secret")


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
        """Refuse to boot with a known placeholder secret once Postgres is in play.

        The dev default is intentionally committed so a fresh clone runs with no
        setup, but shipping it would let anyone mint valid admin tokens.
        """
        if self.database_url.startswith("sqlite"):
            return self

        secret = self.secret_key
        if secret in _KNOWN_PLACEHOLDER_SECRETS:
            raise ValueError(
                "SECRET_KEY is a known placeholder (it is committed in this repo) "
                "while DATABASE_URL points at a non-SQLite database. Set a unique "
                "SECRET_KEY (>= 32 random bytes) before deploying. Generate one "
                'with: python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )

        lowered = secret.lower()
        if any(marker in lowered for marker in _PLACEHOLDER_MARKERS):
            raise ValueError(
                "SECRET_KEY looks like a placeholder while DATABASE_URL points at "
                "a non-SQLite database. Set a unique SECRET_KEY (>= 32 random bytes) "
                'before deploying. Generate one with: python -c '
                '"import secrets; print(secrets.token_urlsafe(48))"'
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