"""Shared helpers for creating in-app notifications from business events."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


async def mirror_inapp_notifications(
    session: AsyncSession,
    user_id: uuid.UUID,
    items: list[dict],
) -> int:
    """Persist in-app NotificationModel rows for alert events.

    Each item must contain ``type``, ``title``, ``body`` and optionally ``data``.
    Returns the number of notifications created.
    """
    from app.infrastructure.repositories.notification_repository import NotificationRepository

    repo = NotificationRepository(session)
    for item in items:
        await repo.create(
            user_id=user_id,
            channel="push",
            type=item["type"],
            title=item["title"],
            body=item["body"],
            data=item.get("data"),
            is_sent=True,
        )
    return len(items)
