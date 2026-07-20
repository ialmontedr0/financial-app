"""Use case: Process due recurring incomes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository
from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ProcessRecurringIncomeUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tx_repo = TransactionRepository(session)
        self._income_repo = IncomeRepository(session)

    async def execute(self) -> dict:
        from datetime import date as date_type, timedelta

        due_items = await self._tx_repo.get_due_recurring()
        income_due = [r for r in due_items if r.transaction_type == "income"]

        processed = []
        errors = []

        for rec in income_due:
            try:
                tx = await self._tx_repo.create(
                    rec.user_id,
                    account_id=rec.account_id,
                    category_id=rec.category_id,
                    subcategory_id=rec.subcategory_id,
                    transaction_type="income",
                    status="completed",
                    amount=rec.amount,
                    currency_code=rec.currency_code,
                    description=rec.description,
                    effective_date=date_type.today(),
                    source="recurring",
                )

                await self._tx_repo.update_account_balance(rec.account_id, rec.amount, "add")

                await self._income_repo.create_income(
                    rec.user_id,
                    transaction_id=tx.id,
                    income_type="other",
                    income_status="received",
                    stability="fixed",
                    effective_date=date_type.today(),
                )

                frequency_days = {"daily": 1, "weekly": 7, "biweekly": 14, "monthly": 30, "quarterly": 90, "yearly": 365}
                days = frequency_days.get(rec.frequency, 30)
                next_date = date_type.today() + timedelta(days=days)

                await self._tx_repo.update_recurring(rec.id, rec.user_id, last_execution_date=date_type.today(), next_execution_date=next_date)

                processed.append({"recurring_id": str(rec.id), "transaction_id": str(tx.id), "amount": str(tx.amount)})
            except Exception as e:
                errors.append({"recurring_id": str(rec.id), "error": str(e)})

        return {
            "processed": len(processed),
            "errors": len(errors),
            "transactions": processed,
            "error_details": errors,
        }
