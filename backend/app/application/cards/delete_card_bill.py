"""Use case: Soft delete a credit card bill."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteCardBillUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(self, user_id: uuid.UUID, card_id: uuid.UUID, bill_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        card = await self._repo.get_card_by_id(card_id, user_id)
        if card is None:
            raise NotFoundError("CreditCard")

        deleted = await self._repo.delete_bill(bill_id, user_id)
        if not deleted:
            raise NotFoundError("CardBill")

        return {"message": "Bill deleted successfully"}
