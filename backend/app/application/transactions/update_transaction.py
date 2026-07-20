"""Use case: Update a transaction with balance adjustment and audit."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class UpdateTransactionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, transaction_id: uuid.UUID, *, changes: dict[str, Any],
        ip_address: str | None = None, user_agent: str | None = None,
    ) -> dict:
        from app.middleware.error_handler import NotFoundError

        tx = await self._repo.get_by_id(transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction")

        audit_changes: dict[str, dict[str, str | None]] = {}
        for field, new_value in changes.items():
            if field in ("amount", "description", "notes", "category_id", "subcategory_id", "status", "effective_date", "account_id"):
                old_value = getattr(tx, field, None)
                if str(old_value) != str(new_value):
                    audit_changes[field] = {"old": str(old_value) if old_value is not None else None, "new": str(new_value) if new_value is not None else None}

        if not audit_changes:
            return {"message": "No changes detected"}

        if "amount" in changes or "account_id" in changes:
            old_amount = tx.amount
            new_amount = Decimal(str(changes.get("amount", tx.amount))) if "amount" in changes else tx.amount
            if tx.transaction_type == "income" and tx.status == "completed":
                await self._repo.update_account_balance(tx.account_id, old_amount, "subtract")
                new_acc = changes.get("account_id", tx.account_id)
                await self._repo.update_account_balance(new_acc, new_amount, "add")
            elif tx.transaction_type == "expense" and tx.status == "completed":
                await self._repo.update_account_balance(tx.account_id, old_amount, "add")
                new_acc = changes.get("account_id", tx.account_id)
                await self._repo.update_account_balance(new_acc, new_amount, "subtract")

        updated = await self._repo.update(transaction_id, user_id, **changes)
        if updated is None:
            raise NotFoundError("Transaction")

        await self._repo.create_audit_log(tx_id=transaction_id, user_id=user_id, action="updated",
            changes=audit_changes, ip_address=ip_address, user_agent=user_agent,
        )

        tags = await self._repo.get_tags(tx.id)
        return {
            "id": str(updated.id), "transaction_type": updated.transaction_type, "status": updated.status,
            "amount": str(updated.amount), "currency_code": updated.currency_code,
            "description": updated.description, "notes": updated.notes,
            "effective_date": updated.effective_date.isoformat() if updated.effective_date else None,
            "tags": [t.tag_name for t in tags],
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
            "audit_changes": audit_changes,
        }
