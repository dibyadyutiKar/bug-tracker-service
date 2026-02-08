"""Redis connection configuration."""

from typing import AsyncGenerator, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config.settings import settings


class RedisClient:
    """Redis client wrapper for connection management."""

    def __init__(self):
        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        self._client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()

    @property
    def client(self) -> Redis:
        """Get Redis client instance."""
        if self._client is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client

    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        return await self.client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None,
    ) -> None:
        """Set key-value with optional expiry in seconds."""
        await self.client.set(key, value, ex=ex)

    async def delete(self, key: str) -> None:
        """Delete key."""
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.client.exists(key) > 0

    async def incr(self, key: str) -> int:
        """Increment key value."""
        return await self.client.incr(key)

    async def expire(self, key: str, seconds: int) -> None:
        """Set key expiry."""
        await self.client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """Get key time-to-live."""
        return await self.client.ttl(key)

    async def sadd(self, key: str, *values: str) -> int:
        """Add values to set."""
        return await self.client.sadd(key, *values)

    async def sismember(self, key: str, value: str) -> bool:
        """Check if value is in set."""
        return await self.client.sismember(key, value)


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> AsyncGenerator[RedisClient, None]:
    """Dependency to get Redis client."""
    yield redis_client
