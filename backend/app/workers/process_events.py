"""Event stream consumer - dispatches published domain events to handlers."""

from __future__ import annotations

import json
import os
import socket
import uuid
from contextlib import suppress
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog
from redis.exceptions import ResponseError

from app.infrastructure.cache.redis import redis_client
from app.infrastructure.eventbus import EVENT_STREAM, EVENT_WORKER_GROUP
from app.infrastructure.models.domain_event import DomainEventModel
from app.workers.handlers import (
    handle_budget_event,
    handle_goal_event,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


async def _ensure_group() -> None:
    with suppress(ResponseError):
        await redis_client.xgroup_create(EVENT_STREAM, EVENT_WORKER_GROUP, id="0", mkstream=True)


def _parse_event(fields: dict[str, Any]) -> dict[str, Any]:
    try:
        data = json.loads(fields.get("data", "{}"))
    except (TypeError, ValueError):
        data = {}
    return {
        "event_id": fields.get("event_id", ""),
        "event_type": fields.get("event_type", ""),
        "aggregate_id": fields.get("aggregate_id", ""),
        "aggregate_type": fields.get("aggregate_type", ""),
        "user_id": fields.get("user_id", ""),
        "data": data,
    }


async def _dispatch(session: AsyncSession, event: dict[str, Any]) -> None:
    await handle_budget_event(session, event)
    await handle_goal_event(session, event)


async def _record_processed(session: AsyncSession, fields: dict[str, Any]) -> None:
    try:
        aggregate_id = (
            uuid.UUID(str(fields.get("aggregate_id", ""))) if fields.get("aggregate_id") else None
        )
        user_id = uuid.UUID(str(fields.get("user_id", ""))) if fields.get("user_id") else None
        if aggregate_id is None:
            return
        session.add(
            DomainEventModel(
                event_type=str(fields.get("event_type", "")),
                aggregate_id=aggregate_id,
                aggregate_type=str(fields.get("aggregate_type", "")),
                user_id=user_id,
                data=_parse_event(fields).get("data"),
                status="processed",
                processed_at=datetime.now(UTC),
            )
        )
    except (ValueError, TypeError):
        logger.warning("event_audit_skipped", reason="invalid_payload")


async def process_events(ctx: dict[str, Any]) -> int:
    """Consume pending and new events from the stream, then ack them.

    Intended to run as an arq cron job. Messages that raise are left pending
    for retry on the next run.
    """
    session: AsyncSession = ctx["db"]
    await _ensure_group()

    consumer = f"{socket.gethostname()}-{os.getpid()}"
    processed = 0

    for read_from in ("0", ">"):
        raw = await redis_client.xreadgroup(
            EVENT_WORKER_GROUP, consumer, {EVENT_STREAM: read_from}, count=100
        )
        if not raw:
            continue

        for _stream, messages in raw:
            for message_id, fields in messages:
                try:
                    event = _parse_event(fields)
                    await _dispatch(session, event)
                    await _record_processed(session, fields)
                    await session.commit()
                except Exception:
                    await session.rollback()
                    logger.exception("event_processing_error", message_id=message_id)
                    continue

                await redis_client.xack(EVENT_STREAM, EVENT_WORKER_GROUP, message_id)
                await redis_client.xdel(EVENT_STREAM, message_id)
                processed += 1

    if processed:
        logger.info("events_processed", count=processed)
    return processed
