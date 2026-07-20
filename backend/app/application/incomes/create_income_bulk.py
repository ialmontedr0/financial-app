"""Use case: Create multiple incomes at once."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository
from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateIncomeBulkUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tx_repo = TransactionRepository(session)
        self._income_repo = IncomeRepository(session)

    async def execute(self, user_id: uuid.UUID, incomes: list[dict]) -> dict:
        from datetime import date as date_type
        from decimal import Decimal

        from app.middleware.error_handler import ValidationError

        created = []
        errors = []

        for i, inc in enumerate(incomes):
            try:
                amount = Decimal(str(inc["amount"]))
                if amount <= 0:
                    raise ValidationError(f"Income #{i + 1}: amount debe ser > 0")

                ed = inc["effective_date"]
                if isinstance(ed, str):
                    ed = date_type.fromisoformat(ed)

                tx = await self._tx_repo.create(
                    user_id,
                    account_id=inc["account_id"],
                    transaction_type="income",
                    status=inc.get("status", "completed"),
                    amount=amount,
                    currency_code=inc.get("currency_code", "DOP"),
                    description=inc["description"],
                    effective_date=ed,
                    category_id=inc.get("category_id"),
                    subcategory_id=inc.get("subcategory_id"),
                    notes=inc.get("notes"),
                    source=inc.get("source", "import"),
                )

                if tx.status == "completed":
                    await self._tx_repo.update_account_balance(inc["account_id"], amount, "add")

                income = await self._income_repo.create_income(
                    user_id,
                    transaction_id=tx.id,
                    income_type=inc.get("income_type", "other"),
                    income_status=inc.get("income_status", "received"),
                    stability=inc.get("stability", "one_time"),
                    income_source_id=inc.get("income_source_id"),
                    employer_name=inc.get("employer_name"),
                    gross_amount=Decimal(str(inc["gross_amount"])) if inc.get("gross_amount") else None,
                    tax_withheld=Decimal(str(inc["tax_withheld"])) if inc.get("tax_withheld") else None,
                    net_amount=Decimal(str(inc["net_amount"])) if inc.get("net_amount") else None,
                    frequency=inc.get("frequency"),
                    effective_date=ed,
                    notes=inc.get("notes"),
                )

                created.append({"id": str(income.id), "transaction_id": str(tx.id), "description": tx.description, "amount": str(tx.amount)})
            except Exception as e:
                errors.append({"index": i, "error": str(e), "data": inc})

        return {
            "created": len(created),
            "errors": len(errors),
            "incomes": created,
            "error_details": errors,
        }
