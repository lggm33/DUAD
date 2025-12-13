from __future__ import annotations

from typing import Optional

from flask import Flask
import redis

from app.config.settings import Settings


class RedisClient:
    def __init__(self) -> None:
        self._client: Optional[redis.Redis] = None

    def init_app(self, app: Flask, settings: Settings) -> None:
        client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )

        self._client = client

    def get_client(self) -> redis.Redis:
        if self._client is None:
            raise RuntimeError("Redis client is not initialized. Call init_app first.")

        return self._client

    def ping(self) -> bool:
        client = self.get_client()
        return bool(client.ping())


