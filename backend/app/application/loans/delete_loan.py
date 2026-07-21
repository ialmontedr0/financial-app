"""Delete loan (soft)."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.loan_repository import LoanRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class DeleteLoanUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LoanRepository(session)

    async def execute(self, user_id: uuid.UUID, loan_id: uuid.UUID) -> dict:
        loan = await self._repo.get_loan(loan_id, user_id)
        if not loan:
            raise NotFoundError("Loan")
        await self._repo.delete_loan(loan)
        return {"message": "Loan deleted successfully"}
