from __future__ import annotations

from functools import lru_cache

from app.config.settings import Settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_environment()


