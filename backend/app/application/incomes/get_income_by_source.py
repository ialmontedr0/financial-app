"""Use case: Get income breakdown by source."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetIncomeBySourceUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncomeRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        date_from: date,
        date_to: date,
    ) -> dict:
        from app.middleware.error_handler import ValidationError

        if date_from > date_to:
            raise ValidationError("date_from debe ser menor o igual que date_to")

        by_source = await self._repo.get_income_by_source(user_id, date_from, date_to)
        return {"sources": by_source, "total_sources": len(by_source)}
