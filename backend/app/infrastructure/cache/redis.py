from typing import Any

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()

# Connection pool
redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL, max_connections=settings.REDIS_MAX_CONNECTIONS, decode_responses=True
)

# Async client
redis_client = redis.Redis(connection_pool=redis_pool)


async def get_redis() -> redis.Redis:
    """Dependencia para FastAPI."""
    return redis_client


async def cache_get(key: str) -> Any | None:
    """Obtener valor desde el cache."""
    return await redis_client.get(key)


async def cache_set(key: str, value: str, ttl: int = 300) -> None:
    """Establecer valor en cache con TTL (segundos)."""
    await redis_client.setex(key, ttl, value)


async def cache_delete(key: str) -> None:
    """Elimina valor desde el cache."""
    await redis_client.delete(key)


async def cache_flush(pattern: str = "*") -> None:
    """Flush cache por patron."""
    keys = []
    async for key in redis_client.scan_iter(match=pattern):
        keys.append(key)
    if keys:
        await redis_client.delete(*keys)
