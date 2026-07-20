"""Use case: Create multiple expenses at once."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateExpenseBulkUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, expenses: list[dict]) -> dict:
        from datetime import date as date_type
        from decimal import Decimal

        from app.middleware.error_handler import ValidationError

        created = []
        errors = []

        for i, exp in enumerate(expenses):
            try:
                amount = Decimal(str(exp["amount"]))
                if amount <= 0:
                    raise ValidationError(f"Expense #{i + 1}: amount debe ser > 0")

                ed = exp["effective_date"]
                if isinstance(ed, str):
                    ed = date_type.fromisoformat(ed)

                tx = await self._repo.create(
                    user_id,
                    account_id=exp["account_id"],
                    transaction_type="expense",
                    status=exp.get("status", "completed"),
                    amount=amount,
                    currency_code=exp.get("currency_code", "DOP"),
                    description=exp["description"],
                    effective_date=ed,
                    category_id=exp.get("category_id"),
                    subcategory_id=exp.get("subcategory_id"),
                    notes=exp.get("notes"),
                    source=exp.get("source", "import"),
                )

                if tx.status == "completed":
                    await self._repo.update_account_balance(exp["account_id"], amount, "subtract")

                created.append(
                    {"id": str(tx.id), "description": tx.description, "amount": str(tx.amount)}
                )
            except Exception as e:
                errors.append({"index": i, "error": str(e), "data": exp})

        return {
            "created": len(created),
            "errors": len(errors),
            "transactions": created,
            "error_details": errors,
        }
