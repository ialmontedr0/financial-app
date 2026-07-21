from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.notification import NotificationModel
from app.infrastructure.models.notification_preference import NotificationPreferenceModel


class NotificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_user_preferences(self, user_id: UUID) -> NotificationPreferenceModel | None:
        result = await self._db.execute(
            select(NotificationPreferenceModel).where(NotificationPreferenceModel.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert_preferences(
        self, user_id: UUID, data: dict[str, Any]
    ) -> NotificationPreferenceModel:
        existing = await self.get_user_preferences(user_id)
        if existing:
            for k, v in data.items():
                if hasattr(existing, k):
                    setattr(existing, k, v)
            await self._db.flush()
            return existing
        pref = NotificationPreferenceModel(user_id=user_id, **data)
        self._db.add(pref)
        await self._db.flush()
        return pref

    async def create(self, **kwargs: Any) -> NotificationModel:
        notif = NotificationModel(**kwargs)
        self._db.add(notif)
        await self._db.flush()
        return notif

    async def get_by_id(self, notification_id: UUID, user_id: UUID) -> NotificationModel | None:
        result = await self._db.execute(
            select(NotificationModel).where(
                and_(
                    NotificationModel.id == notification_id,
                    NotificationModel.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_user(
        self,
        user_id: UUID,
        *,
        channel: str | None = None,
        type_: str | None = None,
        is_read: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[NotificationModel]:
        query = select(NotificationModel).where(NotificationModel.user_id == user_id)
        if channel:
            query = query.where(NotificationModel.channel == channel)
        if type_:
            query = query.where(NotificationModel.type == type_)
        if is_read is not None:
            query = query.where(NotificationModel.is_read == is_read)
        query = query.order_by(NotificationModel.created_at.desc()).offset(skip).limit(limit)
        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> bool:
        notif = await self.get_by_id(notification_id, user_id)
        if not notif:
            return False
        notif.is_read = True
        await self._db.flush()
        return True

    async def bulk_mark_read(self, ids: list[UUID], user_id: UUID) -> int:
        result = await self._db.execute(
            select(NotificationModel).where(
                and_(
                    NotificationModel.id.in_(ids),
                    NotificationModel.user_id == user_id,
                )
            )
        )
        count = 0
        for n in result.scalars().all():
            n.is_read = True
            count += 1
        await self._db.flush()
        return count

    async def delete(self, notification_id: UUID, user_id: UUID) -> bool:
        notif = await self.get_by_id(notification_id, user_id)
        if not notif:
            return False
        await self._db.delete(notif)
        await self._db.flush()
        return True

    async def unread_count(self, user_id: UUID) -> int:
        result = await self._db.execute(
            select(func.count(NotificationModel.id)).where(
                and_(
                    NotificationModel.user_id == user_id,
                    NotificationModel.is_read == False,  # noqa: E712
                )
            )
        )
        return result.scalar() or 0

    async def stats(self, user_id: UUID) -> dict[str, Any]:
        total_q = await self._db.execute(
            select(func.count(NotificationModel.id)).where(
                NotificationModel.user_id == user_id
            )
        )
        total = total_q.scalar() or 0
        unread = await self.unread_count(user_id)

        ch_q = await self._db.execute(
            select(NotificationModel.channel, func.count(NotificationModel.id))
            .where(NotificationModel.user_id == user_id)
            .group_by(NotificationModel.channel)
        )
        by_channel: dict[str, int] = dict(ch_q.all())

        tp_q = await self._db.execute(
            select(NotificationModel.type, func.count(NotificationModel.id))
            .where(NotificationModel.user_id == user_id)
            .group_by(NotificationModel.type)
        )
        by_type: dict[str, int] = dict(tp_q.all())

        return {"total": total, "unread": unread, "by_channel": by_channel, "by_type": by_type}
