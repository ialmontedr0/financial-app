"""Unit tests for RateLimitService using an in-memory fake Redis."""

from __future__ import annotations

import time
from typing import Any

import pytest

from app.infrastructure.rate_limit.rate_limit_service import RateLimitService


class FakeRedisPipeline:
    def __init__(self, client: FakeRedis) -> None:
        self._client = client
        self._ops: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def zremrangebyscore(self, key: str, min_: int, max_: int) -> FakeRedisPipeline:
        self._ops.append(("zremrangebyscore", (key, min_, max_), {}))
        return self

    def zadd(self, key: str, mapping: dict[str, int]) -> FakeRedisPipeline:
        self._ops.append(("zadd", (key, mapping), {}))
        return self

    def zrange(
        self, key: str, start: int, stop: int, withscores: bool = False
    ) -> FakeRedisPipeline:
        self._ops.append(("zrange", (key, start, stop), {"withscores": withscores}))
        return self

    def zcard(self, key: str) -> FakeRedisPipeline:
        self._ops.append(("zcard", (key,), {}))
        return self

    def expire(self, key: str, seconds: int) -> FakeRedisPipeline:
        self._ops.append(("expire", (key, seconds), {}))
        return self

    def delete(self, key: str) -> FakeRedisPipeline:
        self._ops.append(("delete", (key,), {}))
        return self

    async def execute(self) -> list[Any]:
        results = []
        for op, args, kwargs in self._ops:
            result = getattr(self._client, op)(*args, **kwargs)
            results.append(await result if hasattr(result, "__await__") else result)
        return results


class FakeRedis:
    def __init__(self) -> None:
        self._zsets: dict[str, dict[str, float]] = {}

    def pipeline(self) -> FakeRedisPipeline:
        return FakeRedisPipeline(self)

    async def zremrangebyscore(self, key: str, min_: int, max_: int) -> int:
        zset = self._zsets.setdefault(key, {})
        removed = [m for m, s in zset.items() if min_ <= int(s) <= max_]
        for member in removed:
            del zset[member]
        return len(removed)

    async def zadd(self, key: str, mapping: dict[str, int]) -> int:
        zset = self._zsets.setdefault(key, {})
        for member, score in mapping.items():
            zset[member] = float(score)
        return len(mapping)

    async def zrange(self, key: str, start: int, stop: int, withscores: bool = False) -> list[Any]:
        zset = self._zsets.get(key, {})
        ordered = sorted(zset.items(), key=lambda item: item[1])
        selected = ordered[start : stop + 1] if stop >= 0 else ordered[start:]
        if withscores:
            return [(member, score) for member, score in selected]
        return [member for member, _ in selected]

    async def zcard(self, key: str) -> int:
        return len(self._zsets.get(key, {}))

    async def expire(self, key: str, seconds: int) -> bool:  # noqa: ARG002
        return key in self._zsets

    async def delete(self, *keys: str) -> int:
        count = 0
        for key in keys:
            if key in self._zsets:
                del self._zsets[key]
                count += 1
        return count


@pytest.mark.unit
class TestRateLimitService:
    async def test_build_key(self) -> None:
        assert RateLimitService.build_key("auth", "user:1") == "ratelimit:auth:user:1"

    async def test_allows_requests_below_limit(self) -> None:
        service = RateLimitService(FakeRedis())
        key = "ratelimit:test:1"

        allowed, count, retry_after = await service.check_rate_limit(key, max_requests=3)
        assert allowed is True
        assert count == 1
        assert retry_after == 0

        allowed, count, _ = await service.check_rate_limit(key, max_requests=3)
        assert allowed is True
        assert count == 2

    async def test_blocks_when_limit_reached(self) -> None:
        service = RateLimitService(FakeRedis())
        key = "ratelimit:test:1"

        await service.check_rate_limit(key, max_requests=2)
        await service.check_rate_limit(key, max_requests=2)
        allowed, count, retry_after = await service.check_rate_limit(key, max_requests=2)

        assert allowed is False
        assert count == 3
        assert retry_after > 0

    async def test_sliding_window_prunes_expired_members(self) -> None:
        service = RateLimitService(FakeRedis())
        key = "ratelimit:test:1"
        old_score = int(time.time()) - 100
        fake = FakeRedis()
        await fake.zadd(key, {"old": old_score})
        service = RateLimitService(fake)

        allowed, count, _ = await service.check_rate_limit(key, max_requests=2, window_seconds=60)
        assert allowed is True
        assert count == 1

    async def test_get_remaining(self) -> None:
        service = RateLimitService(FakeRedis())
        key = "ratelimit:test:1"

        await service.check_rate_limit(key, max_requests=5)
        assert await service.get_remaining(key, max_requests=5) == 4

    async def test_reset_clears_key(self) -> None:
        service = RateLimitService(FakeRedis())
        key = "ratelimit:test:1"

        await service.check_rate_limit(key, max_requests=5)
        await service.reset(key)
        assert await service.get_remaining(key, max_requests=5) == 5
