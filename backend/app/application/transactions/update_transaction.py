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

    async def execute(
        self,
        user_id: uuid.UUID,
        transaction_id: uuid.UUID,
        *,
        changes: dict[str, Any],
        version: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        from app.middleware.error_handler import ConflictError, NotFoundError

        tx = await self._repo.get_by_id(transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction")

        # Optimistic locking: reject stale writes only when the client sends a version
        if version is not None and tx.version != version:
            raise ConflictError(
                "La transacción fue modificada por otro usuario. Recarga e intenta de nuevo."
            )

        audit_changes: dict[str, dict[str, str | None]] = {}
        for field, new_value in changes.items():
            if field in (
                "amount",
                "description",
                "notes",
                "category_id",
                "subcategory_id",
                "status",
                "effective_date",
                "account_id",
            ):
                old_value = getattr(tx, field, None)
                if str(old_value) != str(new_value):
                    audit_changes[field] = {
                        "old": str(old_value) if old_value is not None else None,
                        "new": str(new_value) if new_value is not None else None,
                    }

        if not audit_changes:
            return {"message": "No changes detected"}

        if not tx.account_id:
            logger.warning("transaction_has_no_account", transaction_id=tx.id)
            return

        if "amount" in changes or "account_id" in changes:
            old_amount = tx.amount
            new_amount = Decimal(str(changes["amount"])) if "amount" in changes else tx.amount
            old_account = tx.account_id
            new_account = changes.get("account_id", old_account)

            if new_amount != old_amount or new_account != old_account:
                if tx.status == "completed":
                    if tx.transaction_type == "income":
                        await self._repo.update_account_balance(old_account, old_amount, "subtract")
                        await self._repo.update_account_balance(new_account, new_amount, "add")
                    elif tx.transaction_type in ("expense", "adjustment"):
                        await self._repo.update_account_balance(old_account, old_amount, "add")
                        await self._repo.update_account_balance(new_account, new_amount, "subtract")

        updated = await self._repo.update(transaction_id, user_id, **changes)
        if updated is None:
            raise NotFoundError("Transaction")

        updated.version += 1
        await self._session.flush()
        await self._session.refresh(updated)

        await self._repo.create_audit_log(
            tx_id=transaction_id,
            user_id=user_id,
            action="updated",
            changes=audit_changes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        tags = await self._repo.get_tags(tx.id)

        # Publish domain event (best-effort, never blocks the update)
        from app.domain.events import EventType
        from app.infrastructure.eventbus import publish_event

        await publish_event(
            event_type=EventType.TRANSACTION_UPDATED,
            aggregate_id=updated.id,
            aggregate_type="transaction",
            user_id=user_id,
            data={
                "transaction_id": str(updated.id),
                "account_id": str(updated.account_id) if updated.account_id else None,
                "category_id": str(updated.category_id) if updated.category_id else None,
                "amount": str(updated.amount),
                "transaction_type": updated.transaction_type,
                "effective_date": updated.effective_date.isoformat()
                if updated.effective_date
                else None,
            },
        )
        return {
            "id": str(updated.id),
            "transaction_type": updated.transaction_type,
            "status": updated.status,
            "version": updated.version,
            "amount": str(updated.amount),
            "currency_code": updated.currency_code,
            "description": updated.description,
            "notes": updated.notes,
            "effective_date": updated.effective_date.isoformat()
            if updated.effective_date
            else None,
            "tags": [t.tag_name for t in tags],
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
            "audit_changes": audit_changes,
        }
