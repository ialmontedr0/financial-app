"""List the user's lent loans (préstamos otorgados)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.lent_loans.serializers import serialize_lent_loan
from app.infrastructure.repositories.lent_loan_repository import LentLoanRepository


class ListLentLoansUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = LentLoanRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict:
        loans = await self._repo.list(user_id, status=status, skip=skip, limit=limit)
        return {
            "items": [serialize_lent_loan(l) for l in loans],
            "total": len(loans),
        }