"""Redis Streams event publisher for the FIP event bus."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog

from app.domain.events import EventType
from app.infrastructure.cache.redis import redis_client

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = structlog.get_logger()

EVENT_STREAM = "domain_events"
EVENT_WORKER_GROUP = "fip-event-workers"
MAX_STREAM_LENGTH = 10000


class EventPublisher:
    """Publishes domain events to the ``domain_events`` Redis stream."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis
        self._stream = EVENT_STREAM

    async def publish(
        self,
        *,
        event_type: EventType | str,
        aggregate_id: uuid.UUID,
        aggregate_type: str,
        user_id: uuid.UUID | None = None,
        data: dict[str, Any] | None = None,
    ) -> str:
        """Append an event to the stream and return its ``event_id``."""
        event_id = str(uuid.uuid4())
        event_value = event_type.value if isinstance(event_type, EventType) else event_type
        payload: dict[str, Any] = {
            "event_id": event_id,
            "event_type": event_value,
            "aggregate_id": str(aggregate_id),
            "aggregate_type": aggregate_type,
            "user_id": str(user_id) if user_id else "",
            "data": json.dumps(data or {}, default=str),
            "created_at": datetime.now(UTC).isoformat(),
        }
        await self._redis.xadd(self._stream, payload, maxlen=MAX_STREAM_LENGTH)  # type: ignore[arg-type]
        return event_id


async def publish_event(
    *,
    event_type: EventType | str,
    aggregate_id: uuid.UUID,
    aggregate_type: str,
    user_id: uuid.UUID | None = None,
    data: dict[str, Any] | None = None,
) -> str | None:
    """Best-effort publish that never blocks or raises for the caller.

    Returns the ``event_id`` when published, otherwise ``None``.
    """
    try:
        publisher = EventPublisher(redis_client)
        event_id = await publisher.publish(
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            user_id=user_id,
            data=data,
        )
    except Exception:
        event_value = event_type.value if isinstance(event_type, EventType) else event_type
        logger.warning("event_publish_failed", event_type=event_value, exc_info=True)
        return None

    if user_id is not None and aggregate_type == "transaction":
        event_value = event_type.value if isinstance(event_type, EventType) else event_type
        if event_value in (EventType.TRANSACTION_CREATED.value, EventType.TRANSACTION_DELETED.value):
            try:
                from app.application.analytics.get_dashboard import invalidate_dashboard

                await invalidate_dashboard(user_id)
            except Exception:
                logger.warning("dashboard_cache_invalidate_failed", user_id=str(user_id), exc_info=True)
    return event_id
