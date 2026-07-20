"""Use case: Process all due recurring transactions (batch job)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ProcessRecurringUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self) -> dict:
        from datetime import UTC, datetime

        from app.domain.transactions.value_objects import RecurrenceFrequency

        due = await self._repo.get_due_recurring()
        created_count = 0
        errors: list[dict] = []

        for rec in due:
            try:
                tx = await self._repo.create(rec.user_id, account_id=rec.account_id,
                    category_id=rec.category_id, subcategory_id=rec.subcategory_id,
                    transaction_type=rec.transaction_type, status="completed", amount=rec.amount,
                    currency_code=rec.currency_code, description=rec.description, notes=rec.notes,
                    effective_date=rec.next_execution_date, source="recurring", recurring_id=rec.id,
                )

                if rec.transaction_type == "income":
                    await self._repo.update_account_balance(rec.account_id, rec.amount, "add")
                elif rec.transaction_type == "expense":
                    await self._repo.update_account_balance(rec.account_id, rec.amount, "subtract")

                await self._repo.create_audit_log(tx_id=tx.id, user_id=rec.user_id, action="created",
                    changes={"recurring": {"recurring_id": str(rec.id), "source": "automatic"}},
                )

                freq = RecurrenceFrequency(rec.frequency)
                new_next = freq.calculate_next_date(rec.next_execution_date, rec.interval)
                new_count = rec.execution_count + 1

                update_kwargs: dict[str, object] = {"next_execution_date": new_next, "execution_count": new_count, "last_executed_at": datetime.now(UTC)}
                if rec.max_executions and new_count >= rec.max_executions:
                    update_kwargs["is_active"] = False
                if rec.end_date and new_next > rec.end_date:
                    update_kwargs["is_active"] = False

                await self._repo.update_recurring(rec.id, rec.user_id, **update_kwargs)
                created_count += 1

            except Exception as e:
                logger.error("recurring_processing_error", recurring_id=str(rec.id), error=str(e))
                errors.append({"recurring_id": str(rec.id), "error": str(e)})

        return {"processed": len(due), "created": created_count, "errors": errors}
