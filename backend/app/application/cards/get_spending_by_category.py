"""Use case: Get spending by category for a card."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetSpendingByCategoryUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(
        self, user_id: uuid.UUID, card_id: uuid.UUID,
        period_start: date | None = None, period_end: date | None = None,
    ) -> dict:
        from app.middleware.error_handler import NotFoundError

        card = await self._repo.get_card_by_id(card_id, user_id)
        if card is None:
            raise NotFoundError("CreditCard")

        breakdown = await self._repo.get_spending_by_category(card_id, user_id, period_start, period_end)
        total = sum(float(b["total"]) for b in breakdown)

        return {
            "credit_card_id": str(card_id),
            "period_start": period_start.isoformat() if period_start else None,
            "period_end": period_end.isoformat() if period_end else None,
            "total_spent": str(round(total, 2)),
            "categories": breakdown,
        }
