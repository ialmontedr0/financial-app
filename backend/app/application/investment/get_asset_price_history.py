"""Get price history for an investment asset."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.investment.serializers import serialize_price_point
from app.infrastructure.repositories.investment_repository import InvestmentRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class GetAssetPriceHistoryUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvestmentRepository(session)

    async def execute(self, user_id: uuid.UUID, asset_id: uuid.UUID, limit: int = 90) -> dict[str, Any]:
        asset = await self._repo.get_asset(asset_id, user_id)
        if asset is None:
            raise NotFoundError("Activo")
        points = await self._repo.list_price_history(asset_id, limit=limit)
        logger.info("investment_price_history", asset_id=str(asset_id), points=len(points))
        return {"asset_id": str(asset_id), "points": [serialize_price_point(p) for p in points]}
