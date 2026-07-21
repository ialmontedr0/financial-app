from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import and_, select

from app.core.config import get_settings
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.models.notification import NotificationModel

logger = logging.getLogger(__name__)
settings = get_settings()


async def retry_failed_notifications(ctx: dict) -> None:  # noqa: ARG001
    """Retry notifications that failed to send."""
    async with async_session_factory() as db:
        cutoff = datetime.now(UTC) - timedelta(minutes=30)
        result = await db.execute(
            select(NotificationModel)
            .where(
                and_(
                    NotificationModel.is_sent == False,  # noqa: E712
                    NotificationModel.created_at < cutoff,
                )
            )
            .limit(50)
        )
        failed = list(result.scalars().all())
        if not failed:
            return

        logger.info("Retrying %d failed notifications", len(failed))

        from app.notifications.service import NotificationService

        service = NotificationService(db)

        for notif in failed:
            try:
                await service.send(
                    user_id=notif.user_id,
                    type=notif.type,
                    title=notif.title,
                    body=notif.body,
                    data=notif.data,
                    channels=[notif.channel],
                )
                notif.is_sent = True
                notif.sent_at = datetime.now(UTC)
            except Exception:
                logger.exception("Retry failed for notification %s", notif.id)

        await db.commit()


class WorkerSettings:
    functions = [retry_failed_notifications]
    cron_jobs = [
        cron(retry_failed_notifications, minute={0, 15, 30, 45}),
    ]
    redis_settings = RedisSettings.from_dsn(settings.ARQ_REDIS_URL)
    max_jobs = 10
    job_timeout = 300
    keep_result = 3600
    max_tries = 3
