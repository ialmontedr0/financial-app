"""Create a new investment asset."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.investment.serializers import serialize_asset
from app.domain.investment.value_objects import AssetType, Currency
from app.infrastructure.repositories.investment_repository import InvestmentRepository
from app.middleware.error_handler import ValidationError

logger = structlog.get_logger()


class CreateAssetUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvestmentRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        name: str,
        asset_type: str,
        currency: str = "USD",
        symbol: str | None = None,
        current_price: float | Decimal | None = None,
    ) -> dict[str, Any]:
        try:
            validated_type = AssetType(asset_type)
            validated_currency = Currency(currency)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        if not name or not name.strip():
            raise ValidationError("El nombre del activo es requerido")
        if len(name.strip()) > 200:
            raise ValidationError("El nombre no puede exceder 200 caracteres")
        if symbol and len(symbol.strip()) > 20:
            raise ValidationError("El simbolo no puede exceder 20 caracteres")

        price: Decimal | None = None
        if current_price is not None:
            try:
                price = Decimal(str(current_price))
            except Exception as exc:  # pragma: no cover
                raise ValidationError("El precio actual no es valido") from exc
            if price < 0:
                raise ValidationError("El precio actual no puede ser negativo")

        asset = await self._repo.create_asset(
            user_id=user_id,
            name=name.strip(),
            symbol=symbol.strip() if symbol else None,
            asset_type=validated_type.value,
            currency=validated_currency.value,
            current_price=price,
        )

        logger.info("investment_asset_created", asset_id=str(asset.id), type=asset_type)
        return serialize_asset(asset)
