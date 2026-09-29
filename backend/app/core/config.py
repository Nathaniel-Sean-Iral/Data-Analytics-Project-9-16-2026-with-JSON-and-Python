from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_PLACEHOLDER_SECRETS = {
    "dev-secret-key-change-me",
    "change-me",
    "secret",
    "changeme",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "San Rafael Disaster Preparedness API"
    APP_VERSION: str = "0.2.0"
    API_PREFIX: str = "/api"
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    DEBUG: bool = False

    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    SEED_DEMO_DATA: bool = True
    DEMO_PASSWORD: str = "password"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("SECRET_KEY")
    @classmethod
    def reject_placeholder_secret(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("SECRET_KEY must not be empty")
        if value.strip().lower() in INSECURE_PLACEHOLDER_SECRETS:
            raise ValueError("SECRET_KEY is a known placeholder value; generate a real one")
        return value

    @model_validator(mode="after")
    def require_explicit_secret_in_production(self) -> Settings:
        if self.ENVIRONMENT == "production":
            if "SECRET_KEY" not in self.model_fields_set:
                raise ValueError("SECRET_KEY must be set explicitly when ENVIRONMENT=production")
            if self.SEED_DEMO_DATA:
                raise ValueError("SEED_DEMO_DATA must be disabled when ENVIRONMENT=production")
        return self

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
