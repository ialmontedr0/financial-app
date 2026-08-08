from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog
from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import and_, select, update

from app.core.config import get_settings
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.models.notification import NotificationModel

logger = structlog.get_logger(__name__)
settings = get_settings()

MAX_RETRIES = 3


async def retry_failed_notifications(ctx: dict) -> None:
    """Retry notifications that failed to send.

    Re-envía por el canal directamente sobre la misma fila (sin duplicar
    registros) y limita los reintentos a ``MAX_RETRIES``. Las notificaciones
    agotadas quedan marcadas como no enviadas y no se vuelven a procesar.
    """
    async with async_session_factory() as db:
        cutoff = datetime.now(UTC) - timedelta(minutes=30)
        result = await db.execute(
            select(NotificationModel)
            .where(
                and_(
                    NotificationModel.is_sent == False,  # noqa: E712
                    NotificationModel.retry_count < MAX_RETRIES,
                    NotificationModel.created_at < cutoff,
                )
            )
            .limit(50)
        )
        failed = list(result.scalars().all())
        if not failed:
            return

        logger.info("retrying_failed_notifications", count=len(failed))

        from app.infrastructure.repositories.user_repository import UserRepository
        from app.notifications.channels.email import EmailChannel
        from app.notifications.channels.push import PushChannel
        from app.notifications.service import NotificationService

        channels: dict[str, object] = {
            "email": EmailChannel(),
            "push": PushChannel(),
        }
        service = NotificationService(db)

        for notif in failed:
            try:
                channel = channels.get(notif.channel)
                if channel is None or not channel.is_configured():
                    await db.execute(
                        update(NotificationModel)
                        .where(NotificationModel.id == notif.id)
                        .values(retry_count=notif.retry_count + 1)
                    )
                    continue

                data = dict(notif.data or {})
                if notif.channel == "email" and "email" not in data:
                    user = await UserRepository(db).get_by_id(notif.user_id)
                    if user and user.email:
                        data["email"] = user.email

                message = service._build_message(notif, data=data)
                result = await channel.send(message)

                if result.success:
                    await db.execute(
                        update(NotificationModel)
                        .where(NotificationModel.id == notif.id)
                        .values(is_sent=True, sent_at=datetime.now(UTC), retry_count=0)
                    )
                else:
                    await db.execute(
                        update(NotificationModel)
                        .where(NotificationModel.id == notif.id)
                        .values(retry_count=notif.retry_count + 1)
                    )
                    logger.warning("notification_retry_failed", id=str(notif.id))
            except Exception:
                await db.execute(
                    update(NotificationModel)
                    .where(NotificationModel.id == notif.id)
                    .values(retry_count=notif.retry_count + 1)
                )
                logger.exception("retry_notification_error", id=str(notif.id))

        await db.commit()


class WorkerSettings:
    functions = [retry_failed_notifications]  # noqa: RUF012
    cron_jobs = [  # noqa: RUF012
        cron(retry_failed_notifications, minute={0, 15, 30, 45}),
    ]
    redis_settings = RedisSettings.from_dsn(settings.ARQ_REDIS_URL)
    max_jobs = 10
    job_timeout = 300
    keep_result = 3600
    max_tries = 3
