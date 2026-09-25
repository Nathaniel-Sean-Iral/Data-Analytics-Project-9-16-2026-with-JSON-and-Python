from datetime import timedelta

from app.core.config import settings


def create_fake_token(username: str) -> str:
    return f"mock-token-{username}"


def token_expiration_minutes() -> int:
    return settings.ACCESS_TOKEN_EXPIRE_MINUTES


def token_expiration_delta():
    return timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
