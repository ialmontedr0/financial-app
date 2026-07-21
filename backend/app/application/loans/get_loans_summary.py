"""Get user loans portfolio summary."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.loan_repository import LoanRepository

logger = structlog.get_logger()


class GetLoansSummaryUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LoanRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        summary = await self._repo.get_loans_summary(user_id)
        upcoming = await self._repo.get_upcoming_payments(user_id, days_ahead=30)
        summary["upcoming_payments_30d"] = upcoming
        summary["upcoming_count"] = len(upcoming)
        return summary
