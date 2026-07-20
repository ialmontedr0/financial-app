"""Use case: Update an income with balance adjustment and audit."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository
from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class UpdateIncomeUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tx_repo = TransactionRepository(session)
        self._income_repo = IncomeRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        income_id: uuid.UUID,
        *,
        changes: dict[str, Any],
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        from decimal import Decimal

        from app.middleware.error_handler import NotFoundError, ValidationError

        income = await self._income_repo.get_income_by_id(income_id, user_id)
        if income is None:
            raise NotFoundError("Income")

        tx = await self._tx_repo.get_by_id(income.transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction")
        if tx.transaction_type != "income":
            raise ValidationError("Transaction is not an income")

        tx_fields = {"amount", "description", "notes", "category_id", "subcategory_id", "status", "effective_date", "account_id"}
        income_fields = {"income_type", "income_status", "stability", "income_source_id", "employer_name", "employer_tax_id", "gross_amount", "tax_withheld", "net_amount", "frequency"}

        tx_changes = {k: v for k, v in changes.items() if k in tx_fields}
        income_changes = {k: v for k, v in changes.items() if k in income_fields}

        audit_changes: dict[str, dict[str, str | None]] = {}
        for field, new_value in {**tx_changes, **income_changes}.items():
            old_value = getattr(tx if field in tx_fields else income, field, None)
            if str(old_value) != str(new_value):
                audit_changes[field] = {"old": str(old_value) if old_value is not None else None, "new": str(new_value) if new_value is not None else None}

        if not audit_changes:
            return {"message": "No changes detected"}

        if "amount" in tx_changes or "account_id" in tx_changes:
            old_amount = tx.amount
            new_amount = Decimal(str(tx_changes.get("amount", tx.amount))) if "amount" in tx_changes else tx.amount
            if tx.status == "completed":
                await self._tx_repo.update_account_balance(tx.account_id, old_amount, "subtract")
                new_acc = tx_changes.get("account_id", tx.account_id)
                await self._tx_repo.update_account_balance(new_acc, new_amount, "add")

        if tx_changes:
            await self._tx_repo.update(income.transaction_id, user_id, **tx_changes)

        if income_changes:
            await self._income_repo.update_income(income_id, user_id, **income_changes)

        await self._tx_repo.create_audit_log(
            tx_id=income.transaction_id,
            user_id=user_id,
            action="updated",
            changes=audit_changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        await self._session.refresh(tx)
        tags = await self._tx_repo.get_tags(tx.id)
        updated_income = await self._income_repo.get_income_by_id(income_id, user_id)

        return {
            "id": str(updated_income.id) if updated_income else str(income.id),
            "transaction_id": str(tx.id),
            "status": tx.status,
            "amount": str(tx.amount),
            "currency_code": tx.currency_code,
            "description": tx.description,
            "notes": tx.notes,
            "effective_date": tx.effective_date.isoformat() if tx.effective_date else None,
            "source": tx.source,
            "tags": [t.tag_name for t in tags],
            "income_type": updated_income.income_type if updated_income else income.income_type,
            "income_status": updated_income.income_status if updated_income else income.income_status,
            "stability": updated_income.stability if updated_income else income.stability,
            "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
            "audit_changes": audit_changes,
        }
