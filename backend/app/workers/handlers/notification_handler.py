"""Notification event handler - mirrors domain events as in-app notifications."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from app.domain.events import EventType
from app.infrastructure.repositories.notification_repository import NotificationRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

EVENT_NOTIFICATION_MAP: dict[str, tuple[str, str]] = {
    EventType.TRANSACTION_CREATED.value: (
        "transaction_confirmed",
        "Transaccion de {amount} registrada en {account}",
    ),
}


async def handle_event(session: AsyncSession, event: dict[str, Any]) -> int:
    """Persist an in-app notification for a mapped domain event.

    Returns 1 when a notification is created, otherwise 0.
    """
    event_type = event.get("event_type")
    mapping = EVENT_NOTIFICATION_MAP.get(event_type) if isinstance(event_type, str) else None
    if mapping is None:
        return 0

    user_id_raw = event.get("user_id")
    if not user_id_raw:
        return 0

    try:
        user_id = uuid.UUID(str(user_id_raw))
    except (ValueError, TypeError):
        return 0

    notif_type, template = mapping
    data = event.get("data") or {}
    body = template.format(
        amount=str(data.get("amount", "")),
        account=str(data.get("account") or data.get("account_id") or ""),
    )

    title = notif_type.replace("_", " ").title()

    repo = NotificationRepository(session)
    await repo.create(
        user_id=user_id,
        channel="push",
        type=notif_type,
        title=title,
        body=body,
        data=data,
        is_sent=True,
    )
    return 1
