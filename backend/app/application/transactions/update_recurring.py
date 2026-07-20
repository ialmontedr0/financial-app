"""Use case: Update a recurring pattern."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class UpdateRecurringUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, recurring_id: uuid.UUID, **changes: Any) -> dict:
        from app.middleware.error_handler import NotFoundError

        rec = await self._repo.update_recurring(recurring_id, user_id, **changes)
        if rec is None:
            raise NotFoundError("Recurring Pattern")

        return {"id": str(rec.id), "transaction_type": rec.transaction_type, "amount": str(rec.amount),
            "frequency": rec.frequency, "next_execution_date": rec.next_execution_date.isoformat(),
            "is_active": rec.is_active}
