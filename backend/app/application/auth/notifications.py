"""Helpers de notificaciones de seguridad."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


async def emit_security_notification(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    event: str,
    title: str,
    body: str,
    data: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Emite una notificacion tipo 'security_alert'"""
    from app.notifications.service import NotificationService

    payload: dict = {"event": event}
    if ip_address:
        payload["ip_address"] = ip_address
    if user_agent:
        payload["user_agent"] = user_agent
    if data:
        payload.update(data)

    await NotificationService(session).send(
        user_id=user_id, type="security_alert", title=title, body=body, data=payload
    )
    logger.info("security_notification", user_id=str(user_id), notification_event=event)
