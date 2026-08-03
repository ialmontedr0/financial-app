"""Create an investment transaction (buy/sell/dividend/fee) and update the portfolio."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.investment.serializers import serialize_transaction
from app.domain.investment.value_objects import InvestmentTxType
from app.infrastructure.repositories.investment_repository import InvestmentRepository
from app.middleware.error_handler import NotFoundError, ValidationError

logger = structlog.get_logger()


class CreateInvestmentTransactionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvestmentRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        asset_id: uuid.UUID,
        tx_type: str,
        quantity: float | Decimal,
        price_per_unit: float | Decimal,
        fees: float | Decimal = Decimal("0"),
        portfolio_id: uuid.UUID | None = None,
        tx_date: date | None = None,
        total_amount: float | Decimal | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        try:
            validated_type = InvestmentTxType(tx_type)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        asset = await self._repo.get_asset(asset_id, user_id)
        if asset is None:
            raise NotFoundError("Activo")

        if portfolio_id is not None:
            portfolio = await self._repo.get_portfolio(portfolio_id, user_id)
            if portfolio is None:
                raise NotFoundError("Portafolio")

        try:
            qty = Decimal(str(quantity))
            price = Decimal(str(price_per_unit))
            fee_value = Decimal(str(fees))
        except Exception as exc:  # pragma: no cover
            raise ValidationError("Los valores numericos no son validos") from exc

        if qty <= 0:
            raise ValidationError("La cantidad debe ser mayor a 0")
        if price < 0:
            raise ValidationError("El precio por unidad no puede ser negativo")
        if fee_value < 0:
            raise ValidationError("Las comisiones no pueden ser negativas")

        if total_amount is not None:
            try:
                total = Decimal(str(total_amount))
            except Exception as exc:  # pragma: no cover
                raise ValidationError("El monto total no es valido") from exc
        else:
            base = qty * price
            total = base - fee_value if validated_type.value == "dividend" else base + fee_value
        if total < 0:
            raise ValidationError("El monto total no puede ser negativo")

        effective_date = tx_date or date.today()  # noqa: DTZ011

        # Update portfolio holdings for buy/sell
        if validated_type.value in ("buy", "sell") and portfolio_id is not None:
            pa = await self._repo.get_portfolio_asset(portfolio_id, asset_id)
            if validated_type.value == "buy":
                if pa is None:
                    avg = total / qty if qty > 0 else Decimal("0")
                    await self._repo.add_portfolio_asset(
                        portfolio_id=portfolio_id,
                        asset_id=asset_id,
                        quantity=qty,
                        cost_basis=total,
                        average_price=avg,
                    )
                else:
                    new_qty = pa.quantity + qty
                    new_cost = pa.cost_basis + total
                    avg = new_cost / new_qty if new_qty > 0 else Decimal("0")
                    await self._repo.update_portfolio_asset(
                        pa, quantity=new_qty, cost_basis=new_cost, average_price=avg
                    )
            else:  # sell
                if pa is not None:
                    if pa.quantity < qty:
                        raise ValidationError(
                            "No se puede vender una cantidad mayor a la disponible en el portafolio"
                        )
                    ratio = qty / pa.quantity if pa.quantity > 0 else Decimal("0")
                    remaining_qty = pa.quantity - qty
                    remaining_cost = pa.cost_basis - pa.cost_basis * ratio
                    avg = remaining_cost / remaining_qty if remaining_qty > 0 else Decimal("0")
                    await self._repo.update_portfolio_asset(
                        pa, quantity=remaining_qty, cost_basis=remaining_cost, average_price=avg
                    )

        # Dividends and fees don't change holdings but may set the reference price
        asset = await self._repo.update_asset(asset, current_price=price)

        tx = await self._repo.create_transaction(
            asset_id=asset_id,
            portfolio_id=portfolio_id,
            type=validated_type.value,
            quantity=qty,
            price_per_unit=price,
            total_amount=total,
            fees=fee_value,
            date=effective_date,
            notes=notes,
        )

        logger.info(
            "investment_transaction_created",
            tx_id=str(tx.id),
            type=validated_type.value,
            asset_id=str(asset_id),
        )
        return serialize_transaction(tx)
