import pytest
from pydantic import ValidationError

from app.core.config import Settings

_DEV_SECRET = "dev-only-change-me-in-production-0123456789abcdef"
# The fallback docker-compose.yml ships in ${SECRET_KEY:-...}. It is a different
# string from the dev default, so a guard that only matched _DEV_SECRET let the
# whole compose stack boot with a publicly-known signing key.
_COMPOSE_SECRET = "change-me-in-production-0123456789abcdef0123456789abcdef"
_PG_URL = "postgresql+psycopg://u:p@db:5432/disaster_prep"


def test_dev_defaults_are_usable():
    s = Settings(_env_file=None, database_url="sqlite:///./x.db", secret_key=_DEV_SECRET)
    assert s.api_prefix == "/api"
    assert s.avg_persons_per_household == 4


def test_production_rejects_dev_secret_key():
    """A committed dev secret must never reach a real database."""
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, database_url=_PG_URL, secret_key=_DEV_SECRET)


def test_production_rejects_the_compose_fallback_secret():
    """Regression: the compose default is a distinct string and was accepted."""
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, database_url=_PG_URL, secret_key=_COMPOSE_SECRET)


@pytest.mark.parametrize(
    "key",
    [
        "change-me-in-production",
        "CHANGEME-0123456789abcdef",
        "please-change-me-before-deploying",
        "your-secret-key-goes-here",
        "dev-only-secret",
        "example-secret-key",
    ],
)
def test_production_rejects_placeholder_looking_keys(key):
    """Any obvious placeholder must be caught, not just the two hardcoded ones."""
    with pytest.raises(ValidationError, match="placeholder"):
        Settings(_env_file=None, database_url=_PG_URL, secret_key=key)


def test_production_allows_custom_secret_key():
    s = Settings(
        _env_file=None,
        database_url=_PG_URL,
        secret_key="a-properly-random-secret-key-0123456789",
    )
    assert s.database_url.startswith("postgresql")


def test_sqlite_still_tolerates_the_dev_secret():
    """Local development must not be blocked by the production guard."""
    s = Settings(_env_file=None, database_url="sqlite:///./x.db", secret_key=_COMPOSE_SECRET)
    assert s.secret_key == _COMPOSE_SECRET


def test_wildcard_cors_cannot_be_mixed_with_explicit_origins():
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        Settings(_env_file=None, cors_origins=["*", "https://drrm.gov.ph"])


def test_explicit_cors_origins_allowed():
    s = Settings(_env_file=None, cors_origins=["https://drrm.gov.ph"])
    assert s.cors_origins == ["https://drrm.gov.ph"]
