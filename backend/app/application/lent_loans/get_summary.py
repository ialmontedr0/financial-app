"""Portfolio summary for lent loans (as an investment class)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.lent_loan_repository import LentLoanRepository


class GetLentLoanSummaryUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = LentLoanRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        summary = await self._repo.get_portfolio_summary(user_id)
        summary["asset_class"] = "lent_loan"
        return summary