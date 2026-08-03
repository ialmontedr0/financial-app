"""arq worker settings for the FIP background worker."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import delete

from app.application.transactions.process_recurring import ProcessRecurringUseCase
from app.core.config import get_settings
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.models.notification import NotificationModel
from app.infrastructure.models.user_session import UserSessionModel
from app.infrastructure.workers.notification_worker import retry_failed_notifications
from app.workers.process_events import process_events

logger = structlog.get_logger()
settings = get_settings()


async def startup(ctx: dict[str, Any]) -> dict[str, Any]:
    """Open a database session for the worker lifespan."""
    ctx["db"] = async_session_factory()
    logger.info("worker_started")
    return ctx


async def shutdown(ctx: dict[str, Any]) -> None:
    """Close the worker database session."""
    db = ctx.get("db")
    if db is not None:
        await db.close()
    logger.info("worker_shutdown")


async def process_recurring_transactions(ctx: dict[str, Any]) -> dict[str, Any]:
    """Create transactions for due recurring rules."""
    db = ctx["db"]
    try:
        result = await ProcessRecurringUseCase(db).execute()
        await db.commit()
        logger.info("recurring_transactions_processed", **result)
        return result
    except Exception:
        await db.rollback()
        logger.exception("recurring_transactions_failed")
        raise


async def cleanup_sessions(ctx: dict[str, Any]) -> int:
    """Delete expired user sessions."""
    db = ctx["db"]
    result = await db.execute(
        delete(UserSessionModel).where(UserSessionModel.expires_at < datetime.now(UTC))
    )
    await db.commit()
    logger.info("expired_sessions_cleaned", deleted=result.rowcount or 0)
    return result.rowcount or 0


async def cleanup_notifications(ctx: dict[str, Any]) -> int:
    """Delete read notifications older than 90 days."""
    db = ctx["db"]
    cutoff = datetime.now(UTC) - timedelta(days=90)
    result = await db.execute(
        delete(NotificationModel).where(
            NotificationModel.created_at < cutoff,
            NotificationModel.is_read.is_(True),
        )
    )
    await db.commit()
    logger.info("old_notifications_cleaned", deleted=result.rowcount or 0)
    return result.rowcount or 0


class WorkerSettings:
    """arq WorkerSettings: event consumption plus periodic maintenance jobs."""

    functions: list[Any] = [  # noqa: RUF012
        process_events,
        process_recurring_transactions,
        cleanup_sessions,
        cleanup_notifications,
        retry_failed_notifications,
    ]
    cron_jobs: list[Any] = [  # noqa: RUF012
        cron(process_events, minute={0, 30}, run_at_startup=True),
        cron(process_recurring_transactions, hour={6}, minute={0}),
        cron(cleanup_sessions, hour={3}, minute={0}),
        cron(cleanup_notifications, hour={4}, minute={0}),
        cron(retry_failed_notifications, minute={0, 15, 30, 45}),
    ]
    redis_settings = RedisSettings.from_dsn(settings.ARQ_REDIS_URL)
    max_jobs = 10
    job_timeout = 300
    keep_result = 3600
    max_tries = 3
    on_startup = startup
    on_shutdown = shutdown


__all__ = ["WorkerSettings"]
