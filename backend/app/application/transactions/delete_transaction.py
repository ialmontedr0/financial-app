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

    async def execute(self, user_id: uuid.UUID, transaction_id: uuid.UUID, *,
        ip_address: str | None = None, user_agent: str | None = None,
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

        deleted = await self._repo.soft_delete(transaction_id, user_id)
        if deleted is None:
            raise NotFoundError("Transaction")

        await self._repo.create_audit_log(tx_id=transaction_id, user_id=user_id, action="deleted",
            changes={"deleted": {"amount": str(tx.amount), "type": tx.transaction_type}},
            ip_address=ip_address, user_agent=user_agent,
        )

        return {"id": str(deleted.id), "status": deleted.status, "message": "Transaccion eliminada exitosamente"}
