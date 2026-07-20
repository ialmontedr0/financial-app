"""Use case: Quick income creation with minimal fields."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.application.incomes.create_income import CreateIncomeUseCase

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateQuickIncomeUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._create_uc = CreateIncomeUseCase(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        account_id: uuid.UUID,
        amount: float,
        description: str,
        effective_date: date,
        notes: str | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        return await self._create_uc.execute(
            user_id,
            account_id=account_id,
            amount=amount,
            description=description,
            effective_date=effective_date,
            notes=notes,
            tags=tags,
            income_type="other",
            income_status="received",
            stability="one_time",
        )
