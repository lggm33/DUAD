from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SettingsError(RuntimeError):
    pass


class AppEnvironment(str, Enum):
    STAGING = "staging"
    PRODUCTION = "production"


def _read_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default

    normalized = value.strip().lower()
    truthy = {"1", "true", "yes", "y", "on"}
    falsy = {"0", "false", "no", "n", "off"}

    if normalized in truthy:
        return True
    if normalized in falsy:
        return False

    return default


def _load_dotenv_if_present(env: AppEnvironment) -> None:
    if env == AppEnvironment.PRODUCTION:
        return

    try:
        from dotenv import load_dotenv
    except Exception:
        return

    try:
        load_dotenv(override=False)
    except Exception:
        # Loading .env is a convenience for local development. If the file is not readable
        # (permissions/sandbox), we should not crash the application.
        print("Warning: .env file not found or not readable. Continuing without it.")
        return


def _get_env_name(raw: Optional[str]) -> AppEnvironment:
    if raw is None:
        return AppEnvironment.STAGING

    normalized = raw.strip().lower()
    for candidate in AppEnvironment:
        if normalized == candidate.value:
            return candidate

    return AppEnvironment.STAGING


def _must_get(value: Optional[str], key_name: str) -> str:
    if value is None or value.strip() == "":
        raise SettingsError(f"Missing required environment variable: {key_name}")

    return value.strip()


def _normalize_database_url(raw_url: str) -> str:
    """
    Railway commonly provides DATABASE_URL as `postgresql://...` (or `postgres://...`).
    SQLAlchemy defaults to the psycopg2 driver for `postgresql://`, but this project uses psycopg v3.
    """

    stripped = raw_url.strip()
    if stripped.startswith("postgresql://"):
        return stripped.replace("postgresql://", "postgresql+psycopg://", 1)
    if stripped.startswith("postgres://"):
        return stripped.replace("postgres://", "postgresql+psycopg://", 1)

    return stripped


@dataclass(frozen=True)
class Settings:
    env: AppEnvironment
    debug: bool
    secret_key: str
    database_url: str
    redis_url: str
    sqlalchemy_echo: bool
    
    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires: int = 3600  # 1 hour

    @staticmethod
    def from_environment() -> "Settings":
        env = _get_env_name(os.getenv("APP_ENV"))
        _load_dotenv_if_present(env)

        debug = _read_bool(os.getenv("DEBUG"), default=False)
        sqlalchemy_echo = _read_bool(os.getenv("SQLALCHEMY_ECHO"), default=False)

        secret_key = _must_get(os.getenv("SECRET_KEY"), "SECRET_KEY")
        database_url = _normalize_database_url(_must_get(os.getenv("DATABASE_URL"), "DATABASE_URL"))
        redis_url = _must_get(os.getenv("REDIS_URL"), "REDIS_URL")
        
        # JWT Configuration
        jwt_secret_key = _must_get(os.getenv("JWT_SECRET_KEY"), "JWT_SECRET_KEY")
        jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256").strip()
        jwt_access_token_expires = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))

        return Settings(
            env=env,
            debug=debug,
            secret_key=secret_key,
            database_url=database_url,
            redis_url=redis_url,
            sqlalchemy_echo=sqlalchemy_echo,
            jwt_secret_key=jwt_secret_key,
            jwt_algorithm=jwt_algorithm,
            jwt_access_token_expires=jwt_access_token_expires,
        )


