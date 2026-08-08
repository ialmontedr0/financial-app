"""List the user's outstanding lent loans (cuentas por cobrar)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.lent_loans.serializers import serialize_lent_loan
from app.infrastructure.repositories.lent_loan_repository import LentLoanRepository


class ListReceivablesUseCase:
    """Cuentas por cobrar: préstamos otorgados con saldo pendiente."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = LentLoanRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        loans = await self._repo.list_receivables(user_id)
        overdue = [loan for loan in loans if loan.status == "defaulted"]
        return {
            "items": [serialize_lent_loan(loan) for loan in loans],
            "total": len(loans),
            "summary": {
                "count": len(loans),
                "count_overdue": len(overdue),
                "total_outstanding": sum(float(loan.current_balance) for loan in loans),
                "total_overdue": sum(float(loan.current_balance) for loan in overdue),
                "total_principal": sum(float(loan.principal_amount) for loan in loans),
                "total_received": sum(float(loan.total_received) for loan in loans),
                "total_interest_expected": sum(
                    float(loan.total_interest_expected) for loan in loans
                ),
            },
        }
