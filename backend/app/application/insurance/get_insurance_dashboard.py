"""Get insurance portfolio dashboard."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.insurance_repository import InsuranceRepository

logger = structlog.get_logger()


class GetInsuranceDashboardUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InsuranceRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict[str, Any]:
        dashboard = await self._repo.get_dashboard(user_id)
        logger.info("insurance_dashboard_retrieved", user_id=str(user_id))
        return dashboard
