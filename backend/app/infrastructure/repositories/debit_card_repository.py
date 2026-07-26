"""Repository for debit card persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select

from app.infrastructure.models.debit_card import DebitCardModel

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DebitCardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: uuid.UUID, **kwargs: object) -> DebitCardModel:
        card = DebitCardModel(user_id=user_id, **kwargs)
        self._session.add(card)
        await self._session.flush()
        logger.info("debit_card_created", user_id=str(user_id), card_id=str(card.id))
        return card

    async def get_by_id(self, card_id: uuid.UUID, user_id: uuid.UUID) -> DebitCardModel | None:
        stmt = select(DebitCardModel).where(
            DebitCardModel.id == card_id,
            DebitCardModel.user_id == user_id,
            DebitCardModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> list[DebitCardModel]:
        stmt = (
            select(DebitCardModel)
            .where(DebitCardModel.user_id == user_id, DebitCardModel.deleted_at.is_(None))
            .order_by(DebitCardModel.name.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_account(self, account_id: uuid.UUID, user_id: uuid.UUID) -> list[DebitCardModel]:
        stmt = (
            select(DebitCardModel)
            .where(
                DebitCardModel.account_id == account_id,
                DebitCardModel.user_id == user_id,
                DebitCardModel.deleted_at.is_(None),
            )
            .order_by(DebitCardModel.name.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, card_id: uuid.UUID, user_id: uuid.UUID, **kwargs: object) -> DebitCardModel | None:
        card = await self.get_by_id(card_id, user_id)
        if card is None:
            return None
        for key, value in kwargs.items():
            if hasattr(card, key):
                setattr(card, key, value)
        await self._session.flush()
        await self._session.refresh(card)
        return card

    async def delete(self, card_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime

        card = await self.get_by_id(card_id, user_id)
        if card is None:
            return False
        card.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True
