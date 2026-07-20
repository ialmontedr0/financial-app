"""Use case: Get credit card utilization metrics."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetCardUtilizationUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(self, user_id: uuid.UUID, credit_card_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        utilization = await self._repo.get_card_utilization(credit_card_id, user_id)
        if utilization is None:
            raise NotFoundError("CreditCard")

        return utilization
