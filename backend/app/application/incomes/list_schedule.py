"""Use case: List income schedules."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListScheduleUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncomeRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict:
        schedules = await self._repo.list_schedules(user_id, status=status, date_from=date_from, date_to=date_to)

        items = [
            {
                "id": str(s.id),
                "description": s.description,
                "amount": str(s.amount),
                "currency_code": s.currency_code,
                "account_id": str(s.account_id),
                "expected_date": s.expected_date.isoformat(),
                "status": s.status,
                "frequency": s.frequency,
                "income_source_id": str(s.income_source_id) if s.income_source_id else None,
                "projection_method": s.projection_method,
                "confidence_score": str(s.confidence_score) if s.confidence_score else None,
                "notes": s.notes,
                "received_transaction_id": str(s.received_transaction_id) if s.received_transaction_id else None,
                "received_at": s.received_at.isoformat() if s.received_at else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in schedules
        ]

        return {"schedules": items, "total": len(items)}
