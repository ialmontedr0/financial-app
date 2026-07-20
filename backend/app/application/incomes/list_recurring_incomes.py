"""Use case: List recurring income configurations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListRecurringIncomesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tx_repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, *, is_active: bool | None = None) -> dict:
        recurring = await self._tx_repo.list_recurring(user_id, is_active=is_active)

        income_recurring = [r for r in recurring if r.transaction_type == "income"]

        items = [
            {
                "id": str(r.id),
                "transaction_type": r.transaction_type,
                "frequency": r.frequency,
                "amount": str(r.amount),
                "currency_code": r.currency_code,
                "description": r.description,
                "account_id": str(r.account_id),
                "category_id": str(r.category_id) if r.category_id else None,
                "next_execution_date": r.next_execution_date.isoformat() if r.next_execution_date else None,
                "last_execution_date": r.last_execution_date.isoformat() if r.last_execution_date else None,
                "is_active": r.is_active,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in income_recurring
        ]

        return {"recurring_incomes": items, "total": len(items)}
