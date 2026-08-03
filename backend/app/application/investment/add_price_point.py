"""Add a price point to the asset history and update the current price."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.investment.serializers import serialize_price_point
from app.infrastructure.repositories.investment_repository import InvestmentRepository
from app.middleware.error_handler import NotFoundError, ValidationError

logger = structlog.get_logger()


class AddPricePointUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvestmentRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        asset_id: uuid.UUID,
        close_price: float | Decimal,
        price_date: date | None = None,
        open_price: float | Decimal | None = None,
        high_price: float | Decimal | None = None,
        low_price: float | Decimal | None = None,
        volume: float | Decimal | None = None,
    ) -> dict[str, Any]:
        asset = await self._repo.get_asset(asset_id, user_id)
        if asset is None:
            raise NotFoundError("Activo")

        try:
            close = Decimal(str(close_price))
        except Exception as exc:  # pragma: no cover
            raise ValidationError("El precio de cierre no es valido") from exc
        if close < 0:
            raise ValidationError("El precio de cierre no puede ser negativo")

        def _opt(value: float | Decimal | None) -> Decimal | None:
            if value is None:
                return None
            try:
                return Decimal(str(value))
            except Exception:  # pragma: no cover
                raise ValidationError("Los valores numericos no son validos") from None

        effective_date = price_date or date.today()  # noqa: DTZ011
        point = await self._repo.upsert_price_point(
            asset_id=asset_id,
            price_date=effective_date,
            close_price=close,
            open_price=_opt(open_price),
            high_price=_opt(high_price),
            low_price=_opt(low_price),
            volume=_opt(volume),
        )
        asset = await self._repo.update_asset(asset, current_price=close)

        logger.info(
            "investment_price_point_added", asset_id=str(asset_id), date=effective_date.isoformat()
        )
        return serialize_price_point(point)
