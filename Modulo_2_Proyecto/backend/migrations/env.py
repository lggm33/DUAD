from __future__ import annotations

from logging.config import fileConfig

import os
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

_BASE_DIR = Path(__file__).resolve().parents[1]
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))


def _load_dotenv_if_present() -> None:
    """
    Load .env for local development convenience.

    This is a best-effort operation: migrations should not crash if .env is missing
    or not readable in the current environment.
    """

    if os.getenv("APP_ENV", "").strip().lower() == "production":
        return

    try:
        from dotenv import load_dotenv
    except Exception:
        return

    try:
        load_dotenv(override=False)
    except Exception:
        return


_load_dotenv_if_present()


def _normalize_database_url(raw_url: str) -> str:
    """
    Normalize DATABASE_URL for SQLAlchemy.

    Railway commonly provides DATABASE_URL as `postgresql://...` (or `postgres://...`).
    This project uses psycopg v3, so we want `postgresql+psycopg://...`.
    """

    stripped = raw_url.strip()
    if stripped.startswith("postgresql://"):
        return stripped.replace("postgresql://", "postgresql+psycopg://", 1)
    if stripped.startswith("postgres://"):
        return stripped.replace("postgres://", "postgresql+psycopg://", 1)

    return stripped


# Import models so they are registered in SQLAlchemy's metadata.
from app.domain.common.models import Base  # noqa: E402
import app.domain.users.models  # noqa: E402,F401
import app.domain.auth.models  # noqa: E402,F401

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    env_url = os.getenv("DATABASE_URL")
    if env_url is not None and env_url.strip() != "":
        config.set_main_option("sqlalchemy.url", _normalize_database_url(env_url))

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    env_url = os.getenv("DATABASE_URL")
    if env_url is not None and env_url.strip() != "":
        config.set_main_option("sqlalchemy.url", _normalize_database_url(env_url))

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
