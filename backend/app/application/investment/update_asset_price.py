"""Update the current price of an investment asset."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.investment.serializers import serialize_asset
from app.infrastructure.repositories.investment_repository import InvestmentRepository
from app.middleware.error_handler import NotFoundError, ValidationError

logger = structlog.get_logger()


class UpdateAssetPriceUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvestmentRepository(session)

    async def execute(
        self, user_id: uuid.UUID, asset_id: uuid.UUID, current_price: float | Decimal
    ) -> dict[str, Any]:
        asset = await self._repo.get_asset(asset_id, user_id)
        if asset is None:
            raise NotFoundError("Activo")

        try:
            price = Decimal(str(current_price))
        except Exception as exc:  # pragma: no cover
            raise ValidationError("El precio actual no es valido") from exc
        if price < 0:
            raise ValidationError("El precio actual no puede ser negativo")

        asset = await self._repo.update_asset(asset, current_price=price)
        logger.info("investment_asset_price_updated", asset_id=str(asset_id), price=str(price))
        return serialize_asset(asset)
