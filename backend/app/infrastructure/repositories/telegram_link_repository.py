from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.telegram_link_code import TelegramLinkCodeModel


class TelegramLinkRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, user_id: UUID, code: str, expires_at: datetime) -> TelegramLinkCodeModel:
        link = TelegramLinkCodeModel(user_id=user_id, code=code, expires_at=expires_at)
        self._db.add(link)
        await self._db.flush()
        return link

    async def get_by_code(self, code: str) -> TelegramLinkCodeModel | None:
        result = await self._db.execute(
            select(TelegramLinkCodeModel).where(TelegramLinkCodeModel.code == code)
        )
        return result.scalar_one_or_none()

    async def mark_used(self, link: TelegramLinkCodeModel) -> None:
        link.is_used = True
        await self._db.flush()

    async def get_active_by_user(self, user_id: UUID) -> TelegramLinkCodeModel | None:
        now = datetime.utcnow()
        result = await self._db.execute(
            select(TelegramLinkCodeModel).where(
                and_(
                    TelegramLinkCodeModel.user_id == user_id,
                    TelegramLinkCodeModel.is_used == False,
                    TelegramLinkCodeModel.expires_at > now,
                )
            ).order_by(TelegramLinkCodeModel.created_at.desc())
        )
        return result.scalar_one_or_none()
