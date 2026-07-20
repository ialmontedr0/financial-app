"""Use case: List recurring transaction patterns."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListRecurringUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, *, is_active: bool | None = None) -> dict:
        recs = await self._repo.list_recurring(user_id, is_active=is_active)
        return {"recurring": [{"id": str(r.id), "transaction_type": r.transaction_type, "amount": str(r.amount),
            "currency_code": r.currency_code, "description": r.description, "frequency": r.frequency,
            "interval": r.interval, "start_date": r.start_date.isoformat(),
            "end_date": r.end_date.isoformat() if r.end_date else None,
            "next_execution_date": r.next_execution_date.isoformat(), "execution_count": r.execution_count,
            "max_executions": r.max_executions, "is_active": r.is_active,
            "last_executed_at": r.last_executed_at.isoformat() if r.last_executed_at else None}
            for r in recs], "total": len(recs)}
