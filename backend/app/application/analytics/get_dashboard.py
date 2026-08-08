"""Get consolidated dashboard."""

from __future__ import annotations

import json
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache.redis import (
    cache_delete,
    cache_get,
    cache_set,
    redis_client,
)
from app.infrastructure.repositories.analytics_repository import AnalyticsRepository

logger = structlog.get_logger()

DASHBOARD_TTL = 300
DASHBOARD_CACHE_PREFIX = "analytics:dashboard:"


def dashboard_cache_key(user_id: uuid.UUID, today: str) -> str:
    """Cache key for a user's dashboard (busted daily + on transaction events)."""
    return f"{DASHBOARD_CACHE_PREFIX}{user_id}:{today}"


async def invalidate_dashboard(user_id: uuid.UUID) -> None:
    """Drop all dashboard cache entries for a user (transaction mutations)."""
    prefix = f"{DASHBOARD_CACHE_PREFIX}{user_id}:"
    async for key in redis_client.scan_iter(match=f"{prefix}*"):
        await cache_delete(key)


class GetDashboardUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AnalyticsRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        from app.utils.time import today_in

        today = today_in().isoformat()
        key = dashboard_cache_key(user_id, today)

        cached = await cache_get(key)
        if cached is not None:
            return json.loads(cached)

        data = await self._repo.get_dashboard(user_id)
        try:
            await cache_set(key, json.dumps(data, default=str), ttl=DASHBOARD_TTL)
        except Exception:
            logger.warning("dashboard_cache_set_failed", user_id=str(user_id), exc_info=True)
        return data
