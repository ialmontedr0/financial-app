"""Rate limiting service backed by a Redis sorted set (sliding window)."""

from __future__ import annotations

import time
import uuid

from redis.asyncio import Redis


class RateLimitService:
    """Sliding-window rate limiter.

    Each request adds a member to a sorted set whose score is the current
    unix timestamp. Expired members are pruned so only requests inside the
    active window are counted. The window slides continuously instead of
    restarting on fixed boundaries.
    """

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    @staticmethod
    def build_key(scope: str, identity: str) -> str:
        """Build the Redis key for a scope/identity pair."""
        return f"ratelimit:{scope}:{identity}"

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int, int]:
        """Register one request and return ``(allowed, count, retry_after)``.

        ``count`` is the number of requests in the window after registering
        the current one. ``retry_after`` is the number of seconds until the
        oldest request expires, or 0 when the request is allowed.
        """
        now = int(time.time())
        window_start = now - window_seconds

        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {f"{now}:{uuid.uuid4().hex}": now})
        pipe.zrange(key, 0, 0, withscores=True)
        pipe.expire(key, window_seconds)
        _, _, oldest_entries, _ = await pipe.execute()

        count = await self._redis.zcard(key)
        if count >= max_requests:
            oldest_score = oldest_entries[0][1] if oldest_entries else now
            retry_after = max(1, (int(oldest_score) + window_seconds) - now)
            return False, count, retry_after
        return True, count, 0

    async def get_remaining(self, key: str, max_requests: int, window_seconds: int = 60) -> int:
        """Return the number of requests still allowed in the window."""
        now = int(time.time())
        window_start = now - window_seconds
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        _, count = await pipe.execute()
        return max(0, max_requests - int(count))

    async def reset(self, key: str) -> None:
        """Clear all recorded requests for the key."""
        await self._redis.delete(key)
