"""Redis-backed cache and lightweight rate-limiting helpers."""

from __future__ import annotations

import json
import logging
from typing import Any

import asyncio

from app.config import get_settings

LOGGER = logging.getLogger(__name__)


class CacheService:
    """Lazy Redis client wrapper with graceful fallback behavior."""

    def __init__(self) -> None:
        settings = get_settings()
        self.redis_url = settings.redis_url
        self.timeout_seconds = settings.redis_timeout_seconds
        self.connect_retries = settings.redis_connect_retries
        self._client: Any | None = None
        self._enabled = True

    async def _get_client(self) -> Any | None:
        """Return cached Redis client instance lazily."""

        if not self._enabled:
            return None
        if self._client is not None:
            return self._client

        for attempt in range(1, self.connect_retries + 1):
            try:
                import redis.asyncio as redis

                self._client = redis.from_url(self.redis_url, decode_responses=True)
                await asyncio.wait_for(self._client.ping(), timeout=self.timeout_seconds)
                return self._client
            except Exception:
                LOGGER.warning("Redis connect attempt failed", extra={"attempt": attempt})
                await asyncio.sleep(0.1 * attempt)

        self._enabled = False
        LOGGER.warning("Redis unavailable, cache features disabled")
        return None

    async def is_healthy(self) -> bool:
        """Check Redis connectivity health."""

        client = await self._get_client()
        if client is None:
            return False
        try:
            return bool(await asyncio.wait_for(client.ping(), timeout=self.timeout_seconds))
        except Exception:
            LOGGER.warning("Redis health check failed")
            return False

    async def get_json(self, key: str) -> dict[str, Any] | None:
        """Retrieve JSON payload from Redis key."""

        client = await self._get_client()
        if client is None:
            return None
        try:
            value = await asyncio.wait_for(client.get(key), timeout=self.timeout_seconds)
            if value is None:
                return None
            parsed = json.loads(str(value))
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            LOGGER.warning("Redis get failed", extra={"key": key})
            return None

    async def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int = 60) -> bool:
        """Store JSON payload in Redis with TTL."""

        client = await self._get_client()
        if client is None:
            return False
        try:
            payload = json.dumps(value, default=str)
            await asyncio.wait_for(client.set(key, payload, ex=ttl_seconds), timeout=self.timeout_seconds)
            return True
        except Exception:
            LOGGER.warning("Redis set failed", extra={"key": key})
            return False

    async def get_batch_lookup(self, batch_id: str) -> dict[str, Any] | None:
        """Fetch cached batch lookup payload."""

        return await self.get_json(f"batch:{batch_id}")

    async def set_batch_lookup(self, batch_id: str, payload: dict[str, Any], ttl_seconds: int = 120) -> bool:
        """Cache batch lookup payload."""

        return await self.set_json(f"batch:{batch_id}", payload, ttl_seconds=ttl_seconds)

    async def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """Rate limiting helper using Redis INCR and EXPIRE semantics."""

        client = await self._get_client()
        if client is None:
            return True, 0

        bucket_key = f"rate:{key}:{window_seconds}"
        try:
            count = int(await asyncio.wait_for(client.incr(bucket_key), timeout=self.timeout_seconds))
            if count == 1:
                await asyncio.wait_for(client.expire(bucket_key, window_seconds), timeout=self.timeout_seconds)
            return count <= limit, count
        except Exception:
            LOGGER.warning("Rate limit fallback allow", extra={"key": key})
            return True, 0
