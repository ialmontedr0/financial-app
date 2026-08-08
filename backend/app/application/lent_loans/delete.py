"""Soft-delete a lent loan (préstamo otorgado)."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.lent_loan_repository import LentLoanRepository
from app.middleware.error_handler import NotFoundError
from app.utils.time import today_in

logger = structlog.get_logger()


class DeleteLentLoanUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LentLoanRepository(session)

    async def execute(self, user_id: uuid.UUID, lent_loan_id: uuid.UUID) -> dict:
        loan = await self._repo.get(lent_loan_id, user_id)
        if loan is None:
            raise NotFoundError("Préstamo otorgado")
        await self._repo.soft_delete(loan, today_in())

        # Al eliminar el préstamo, el saldo pendiente que no se recuperó
        # regresa a la cuenta origen (lo ya cobrado ya fue acreditado).
        if loan.account_id and loan.current_balance > 0:
            from app.infrastructure.repositories.transaction_repository import (
                TransactionRepository,
            )

            await TransactionRepository(self._session).update_account_balance(
                loan.account_id, loan.current_balance, "add"
            )

        await self._session.commit()
        logger.info("lent_loan_deleted", lent_loan_id=str(lent_loan_id))
        return {"message": "Préstamo otorgado eliminado"}
