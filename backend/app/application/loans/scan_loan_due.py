"""Use case: Remind users of loan payments due within the next days."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

REMINDER_HORIZON_DAYS = 7


class ScanLoanDueUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self) -> dict:
        from datetime import UTC, datetime

        from sqlalchemy import select

        from app.infrastructure.models.loan import LoanModel
        from app.infrastructure.repositories.notification_repository import (
            NotificationRepository,
        )
        from app.notifications.service import NotificationService

        today = datetime.now(UTC).date()
        horizon = today + timedelta(days=REMINDER_HORIZON_DAYS)

        result = await self._session.execute(
            select(LoanModel).where(
                LoanModel.status == "active",
                LoanModel.deleted_at.is_(None),
                LoanModel.next_payment_date.is_not(None),
                LoanModel.next_payment_date <= horizon,
            )
        )
        loans = result.scalars().all()

        repo = NotificationRepository(self._session)
        service = NotificationService(self._session)
        emitted = 0

        for loan in loans:
            if await repo.exists_with_data(loan.user_id, "payment_due", "loan_id", str(loan.id)):
                continue
            due = loan.next_payment_date
            status = "venció" if due < today else "vence"
            days = (due - today).days
            await service.send(
                user_id=loan.user_id,
                type="payment_due",
                title=f"Pago de préstamo: {loan.name}",
                body=(
                    f"El pago de '{loan.name}' {status} el {due.isoformat()}"
                    f" (hace {abs(days)} días). "
                    f"Cuota: ${float(loan.monthly_payment):,.2f}."
                ),
                data={
                    "loan_id": str(loan.id),
                    "amount": str(loan.monthly_payment),
                    "due_date": due.isoformat(),
                    "link": f"/loans/{loan.id}",
                },
            )
            emitted += 1

        logger.info("loan_due_scanned", loans=len(loans), emitted=emitted)
        return {"loans_found": len(loans), "notified": emitted}
