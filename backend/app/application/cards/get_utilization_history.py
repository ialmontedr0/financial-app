"""Use case: Get historical utilization for a card."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetUtilizationHistoryUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(self, user_id: uuid.UUID, card_id: uuid.UUID, months: int = 6) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        card = await self._repo.get_card_by_id(card_id, user_id)
        if card is None:
            raise NotFoundError("CreditCard")

        if months < 1 or months > 24:
            raise ValidationError("months debe ser entre 1 y 24")

        history = await self._repo.get_historical_utilization(card_id, user_id, months)
        current = await self._repo.calculate_utilization(card_id, user_id)

        return {
            "credit_card_id": str(card_id),
            "current": current,
            "history": history,
            "months": months,
        }
