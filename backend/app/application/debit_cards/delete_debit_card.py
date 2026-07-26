"""Use case: Soft-delete a debit card."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.debit_card_repository import DebitCardRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteDebitCardUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = DebitCardRepository(session)

    async def execute(self, user_id: uuid.UUID, card_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        deleted = await self._repo.delete(card_id, user_id)
        if not deleted:
            raise NotFoundError("DebitCard")

        logger.info("debit_card_deleted", user_id=str(user_id), card_id=str(card_id))
        return {"success": True, "message": "Debit card deleted"}
