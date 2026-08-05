"""Use case: Soft-delete a transaction with balance reversal and audit."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteTransactionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        transaction_id: uuid.UUID,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        tx = await self._repo.get_by_id(transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction")
        if tx.status == "cancelled":
            raise ValidationError("Transaction already cancelled")

        if tx.status == "completed":
            if tx.transaction_type == "income":
                await self._repo.update_account_balance(tx.account_id, tx.amount, "subtract")
            elif tx.transaction_type == "expense":
                await self._repo.update_account_balance(tx.account_id, tx.amount, "add")
            elif tx.transaction_type == "adjustment":
                await self._repo.update_account_balance(tx.account_id, tx.amount, "add")

        deleted = await self._repo.soft_delete(transaction_id, user_id)
        if deleted is None:
            raise NotFoundError("Transaction")

        await self._repo.create_audit_log(
            tx_id=transaction_id,
            user_id=user_id,
            action="deleted",
            changes={"deleted": {"amount": str(tx.amount), "type": tx.transaction_type}},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Publish domain event (best-effort, never blocks the deletion)
        from app.domain.events import EventType
        from app.infrastructure.eventbus import publish_event

        await publish_event(
            event_type=EventType.TRANSACTION_DELETED,
            aggregate_id=transaction_id,
            aggregate_type="transaction",
            user_id=user_id,
            data={
                "transaction_id": str(transaction_id),
                "account_id": str(tx.account_id) if tx.account_id else None,
                "category_id": str(tx.category_id) if tx.category_id else None,
                "amount": str(tx.amount),
                "currency_code": tx.currency_code,
                "transaction_type": tx.transaction_type,
                "effective_date": tx.effective_date.isoformat() if tx.effective_date else None,
            },
        )

        from app.application.transactions.notifications import emit_transaction_notification

        await emit_transaction_notification(
            self._session,
            user_id,
            transaction_id=transaction_id,
            account_id=tx.account_id,
            amount=f"{tx.amount}",
            currency_code=tx.currency_code,
            action="deleted",
        )

        return {
            "id": str(deleted.id),
            "status": deleted.status,
            "message": "Transaccion eliminada exitosamente",
        }
