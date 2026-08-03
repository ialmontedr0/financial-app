"""Get a single investment asset with its transactions."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.investment.serializers import serialize_asset, serialize_transaction
from app.infrastructure.repositories.investment_repository import InvestmentRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class GetAssetUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvestmentRepository(session)

    async def execute(self, user_id: uuid.UUID, asset_id: uuid.UUID) -> dict[str, Any]:
        asset = await self._repo.get_asset(asset_id, user_id)
        if asset is None:
            raise NotFoundError("Activo")
        transactions = await self._repo.list_asset_transactions(asset_id)
        logger.info("investment_asset_retrieved", asset_id=str(asset_id))
        return {
            **serialize_asset(asset),
            "transactions": [serialize_transaction(tx) for tx in transactions],
            "transactions_count": len(transactions),
        }
