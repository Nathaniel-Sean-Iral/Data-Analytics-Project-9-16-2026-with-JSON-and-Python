from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt

from app.core.config import settings

_PBKDF2_ITERATIONS = 600_000
_ALGORITHM = "HS256"
_PASSWORD_SCHEME = "pbkdf2_sha256"
NO_PASSWORD = "!"

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    if not password or len(password) < settings.PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), _PBKDF2_ITERATIONS)
    return f"{_PASSWORD_SCHEME}${_PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not password or not stored or stored == NO_PASSWORD:
        return False
    try:
        scheme, iterations, salt, expected = stored.split("$")
    except ValueError:
        return False
    if scheme != _PASSWORD_SCHEME:
        return False
    try:
        rounds = int(iterations)
        salt_bytes = bytes.fromhex(salt)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, rounds)
    return hmac.compare_digest(candidate.hex(), expected)


def needs_rehash(stored: str | None) -> bool:
    if not stored or stored == NO_PASSWORD:
        return True
    try:
        scheme, iterations, _, _ = stored.split("$")
    except ValueError:
        return True
    return scheme != _PASSWORD_SCHEME or int(iterations) < _PBKDF2_ITERATIONS


def create_token(subject: str, role: str, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)


def create_access_token(subject: str, role: str) -> str:
    return create_token(subject, role, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(subject: str, role: str) -> str:
    return create_token(subject, role, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    """Decode and validate a token. Raises jwt.PyJWTError subclasses on failure."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Expected a {expected_type} token")
    if not payload.get("sub"):
        raise jwt.InvalidTokenError("Token is missing a subject")
    return payload
