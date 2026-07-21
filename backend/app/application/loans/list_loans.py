"""List user loans."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.loan_repository import LoanRepository

logger = structlog.get_logger()


class ListLoansUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LoanRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
        loan_type: str | None = None,
    ) -> dict:
        loans = await self._repo.list_loans(user_id, status=status, loan_type=loan_type)
        items = []
        for loan in loans:
            progress_pct = 0.0
            if loan.principal_amount > 0:
                paid_principal = float(loan.principal_amount) - float(loan.current_balance)
                progress_pct = round(paid_principal / float(loan.principal_amount) * 100, 2)
            items.append(
                {
                    "id": str(loan.id),
                    "name": loan.name,
                    "loan_type": loan.loan_type,
                    "principal_amount": float(loan.principal_amount),
                    "current_balance": float(loan.current_balance),
                    "annual_interest_rate": float(loan.annual_interest_rate),
                    "monthly_payment": float(loan.monthly_payment),
                    "total_paid": float(loan.total_paid),
                    "status": loan.status,
                    "next_payment_date": loan.next_payment_date.isoformat()
                    if loan.next_payment_date
                    else None,
                    "progress_pct": progress_pct,
                    "created_at": loan.created_at.isoformat() if loan.created_at else None,
                }
            )
        return {"loans": items, "total": len(items)}
