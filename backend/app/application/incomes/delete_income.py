"""Use case: Soft-delete an income with balance reversal and audit."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository
from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteIncomeUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tx_repo = TransactionRepository(session)
        self._income_repo = IncomeRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        income_id: uuid.UUID,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        income = await self._income_repo.get_income_by_id(income_id, user_id)
        if income is None:
            raise NotFoundError("Income")

        tx = await self._tx_repo.get_by_id(income.transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction")
        if tx.transaction_type != "income":
            raise ValidationError("Transaction is not an income")
        if tx.status == "cancelled":
            raise ValidationError("Income already cancelled")

        if tx.status == "completed":
            await self._tx_repo.update_account_balance(tx.account_id, tx.amount, "subtract")

        await self._income_repo.delete_income(income_id, user_id)
        await self._tx_repo.soft_delete(income.transaction_id, user_id)

        await self._tx_repo.create_audit_log(
            tx_id=income.transaction_id,
            user_id=user_id,
            action="deleted",
            changes={"deleted": {"amount": str(tx.amount), "source": tx.source, "income_type": income.income_type}},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "id": str(income.id),
            "transaction_id": str(income.transaction_id),
            "status": "cancelled",
            "message": "Income eliminado exitosamente",
        }
