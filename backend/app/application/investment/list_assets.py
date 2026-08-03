"""List investment assets for the current user."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.investment.serializers import serialize_asset
from app.infrastructure.repositories.investment_repository import InvestmentRepository

logger = structlog.get_logger()


class ListAssetsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvestmentRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict[str, Any]:
        assets = await self._repo.list_assets(user_id)
        logger.info("investment_assets_listed", user_id=str(user_id), count=len(assets))
        return {"assets": [serialize_asset(a) for a in assets], "total": len(assets)}
