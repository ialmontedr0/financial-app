"""Delete an investment asset (soft delete)."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.investment_repository import InvestmentRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class DeleteAssetUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvestmentRepository(session)

    async def execute(self, user_id: uuid.UUID, asset_id: uuid.UUID) -> dict[str, Any]:
        asset = await self._repo.get_asset(asset_id, user_id)
        if asset is None:
            raise NotFoundError("Activo")
        await self._repo.delete_asset(asset)
        logger.info("investment_asset_deleted", asset_id=str(asset_id))
        return {"id": str(asset_id), "status": "deleted"}
