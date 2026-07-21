"""Use case: Soft delete a credit card."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteCardUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(self, user_id: uuid.UUID, card_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        deleted = await self._repo.delete_card(card_id, user_id)
        if not deleted:
            raise NotFoundError("CreditCard")

        return {"message": "Credit card deleted successfully"}
