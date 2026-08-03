"""Get tax summary for a fiscal year."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.tax.value_objects import TaxYear
from app.infrastructure.repositories.tax_repository import TaxRepository
from app.middleware.error_handler import ValidationError

logger = structlog.get_logger()


class GetTaxSummaryUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TaxRepository(session)

    async def execute(self, user_id: uuid.UUID, tax_year: int) -> dict[str, Any]:
        try:
            validated_year = TaxYear(tax_year)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        summary = await self._repo.get_tax_summary(user_id, validated_year.value)
        logger.info("tax_summary_retrieved", user_id=str(user_id), year=tax_year)
        return summary
