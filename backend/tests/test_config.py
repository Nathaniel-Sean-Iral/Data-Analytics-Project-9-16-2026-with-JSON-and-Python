import pytest
from pydantic import ValidationError

from app.core.config import Settings

_DEV_SECRET = "dev-only-change-me-in-production-0123456789abcdef"


def test_dev_defaults_are_usable():
    s = Settings(_env_file=None, database_url="sqlite:///./x.db", secret_key=_DEV_SECRET)
    assert s.api_prefix == "/api"
    assert s.avg_persons_per_household == 4


def test_production_rejects_dev_secret_key():
    """A committed dev secret must never reach a real database."""
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(
            _env_file=None,
            database_url="postgresql+psycopg://u:p@db:5432/disaster_prep",
            secret_key=_DEV_SECRET,
        )


def test_production_allows_custom_secret_key():
    s = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://u:p@db:5432/disaster_prep",
        secret_key="a-properly-random-secret-key-0123456789",
    )
    assert s.database_url.startswith("postgresql")


def test_wildcard_cors_cannot_be_mixed_with_explicit_origins():
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        Settings(_env_file=None, cors_origins=["*", "https://drrm.gov.ph"])


def test_explicit_cors_origins_allowed():
    s = Settings(_env_file=None, cors_origins=["https://drrm.gov.ph"])
    assert s.cors_origins == ["https://drrm.gov.ph"]
