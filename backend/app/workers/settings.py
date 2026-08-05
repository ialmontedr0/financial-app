"""arq worker settings for the FIP background worker."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import delete

from app.application.ai.scan_anomalies import ScanAnomaliesUseCase
from app.application.analytics.send_digest import SendDailyDigestUseCase
from app.application.budgets.scan_budgets import ScanBudgetsUseCase
from app.application.cards.scan_card_alerts import ScanCardAlertsUseCase
from app.application.expenses.scan_renewals import ScanSubscriptionRenewalsUseCase
from app.application.loans.scan_loan_due import ScanLoanDueUseCase
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


async def scan_budgets(ctx: dict[str, Any]) -> dict:
    db = ctx["db"]
    try:
        result = await ScanBudgetsUseCase(db).execute()
        await db.commit()
        logger.info("scan_budgets_done", **result)
        return result
    except Exception:
        await db.rollback()
        logger.exception("scan_budgets_failed")
        raise


async def scan_card_alerts(ctx: dict[str, Any]) -> dict:
    db = ctx["db"]
    try:
        result = await ScanCardAlertsUseCase(db).execute()
        await db.commit()
        logger.info("scan_card_alerts_done", **result)
        return result
    except Exception:
        await db.rollback()
        logger.exception("scan_card_alerts_failed")
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


async def scan_anomalies(ctx: dict[str, Any]) -> dict:
    db = ctx["db"]
    try:
        result = await ScanAnomaliesUseCase(db).execute()
        await db.commit()
        logger.info("scan_anomalies_done", **result)
        return result
    except Exception:
        await db.rollback()
        logger.exception("scan_anomalies_failed")
        raise


async def scan_subscription_renewals(ctx: dict[str, Any]) -> dict:
    db = ctx["db"]
    try:
        result = await ScanSubscriptionRenewalsUseCase(db).execute()
        await db.commit()
        logger.info("scan_renewals_done", **result)
        return result
    except Exception:
        await db.rollback()
        logger.exception("scan_renewals_failed")
        raise


async def scan_loan_due(ctx: dict[str, Any]) -> dict:
    db = ctx["db"]
    try:
        result = await ScanLoanDueUseCase(db).execute()
        await db.commit()
        logger.info("scan_loan_due_done", **result)
        return result
    except Exception:
        await db.rollback()
        logger.exception("scan_loan_due_failed")
        raise


async def send_daily_digest(ctx: dict[str, Any]) -> dict:
    db = ctx["db"]
    try:
        result = await SendDailyDigestUseCase(db).execute()
        await db.commit()
        logger.info("daily_digest_done", **result)
        return result
    except Exception:
        await db.rollback()
        logger.exception("weekly_digest_failed")
        raise


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
        scan_budgets,
        scan_card_alerts,
        scan_anomalies,
        scan_subscription_renewals,
        scan_loan_due,
        send_daily_digest,
    ]
    cron_jobs: list[Any] = [  # noqa: RUF012
        cron(process_events, minute={0, 30}, run_at_startup=True),
        cron(process_recurring_transactions, hour={6}, minute={0}),
        cron(scan_budgets, hour={5}, minute={0}),
        cron(scan_card_alerts, hour={7}, minute={0}),
        cron(scan_anomalies, hour={8}, minute={0}),
        cron(scan_subscription_renewals, hour={6}, minute={30}),
        cron(scan_loan_due, hour={6}, minute={45}),
        cron(send_daily_digest, hour={19}, minute={0}),
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
