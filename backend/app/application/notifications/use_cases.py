from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.notification_repository import NotificationRepository
from app.notifications.service import NotificationService


class SendNotificationUseCase:
    def __init__(self, db: AsyncSession) -> None:
        self._service = NotificationService(db)

    async def execute(
        self,
        *,
        user_id: UUID,
        type: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
        channels: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        results = await self._service.send(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            data=data,
            channels=channels,
        )
        return [
            {"success": r.success, "channel": r.channel, "error": r.error} for r in results
        ]


class GetNotificationsUseCase:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = NotificationRepository(db)

    async def execute(
        self,
        *,
        user_id: UUID,
        channel: str | None = None,
        type_: str | None = None,
        is_read: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Any]:
        return await self._repo.list_user(
            user_id,
            channel=channel,
            type_=type_,
            is_read=is_read,
            skip=skip,
            limit=limit,
        )


class GetNotificationUseCase:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = NotificationRepository(db)

    async def execute(self, notification_id: UUID, user_id: UUID) -> Any | None:
        return await self._repo.get_by_id(notification_id, user_id)


class MarkNotificationReadUseCase:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = NotificationRepository(db)

    async def execute(self, notification_id: UUID, user_id: UUID) -> bool:
        return await self._repo.mark_read(notification_id, user_id)


class DeleteNotificationUseCase:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = NotificationRepository(db)

    async def execute(self, notification_id: UUID, user_id: UUID) -> bool:
        return await self._repo.delete(notification_id, user_id)


class GetNotificationPreferencesUseCase:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = NotificationRepository(db)

    async def execute(self, user_id: UUID) -> Any | None:
        return await self._repo.get_user_preferences(user_id)


class UpdateNotificationPreferencesUseCase:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = NotificationRepository(db)

    async def execute(self, user_id: UUID, data: dict[str, Any]) -> Any:
        return await self._repo.upsert_preferences(user_id, data)


class SendTestNotificationUseCase:
    def __init__(self, db: AsyncSession) -> None:
        self._service = NotificationService(db)

    async def execute(self, user_id: UUID, email: str) -> list[dict[str, Any]]:
        results = await self._service.send(
            user_id=user_id,
            type="system",
            title="Notificacion de Prueba",
            body="Esta es una notificacion de prueba del sistema Financial Intelligence Platform.",
            data={"email": email},
        )
        return [
            {"success": r.success, "channel": r.channel, "error": r.error} for r in results
        ]


class GetNotificationStatsUseCase:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = NotificationRepository(db)

    async def execute(self, user_id: UUID) -> dict[str, Any]:
        return await self._repo.stats(user_id)


class BulkMarkNotificationsReadUseCase:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = NotificationRepository(db)

    async def execute(self, notification_ids: list[UUID], user_id: UUID) -> int:
        return await self._repo.bulk_mark_read(notification_ids, user_id)
