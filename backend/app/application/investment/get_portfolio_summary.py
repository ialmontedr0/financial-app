"""Portfolio summary aggregating value, cost, gain/loss and allocation."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.investment.value_objects import PortfolioSummary
from app.infrastructure.repositories.investment_repository import InvestmentRepository

logger = structlog.get_logger()


class GetPortfolioSummaryUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvestmentRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict[str, Any]:
        portfolios = await self._repo.list_portfolios(user_id)
        portfolio_ids = [p.id for p in portfolios]

        total_value = Decimal("0")
        total_cost = Decimal("0")
        allocation: dict[str, Decimal] = {}
        holdings: list[dict[str, Any]] = []

        if portfolio_ids:
            portfolio_assets = await self._repo.list_assets_in_portfolios(portfolio_ids)
            asset_ids = list({pa.asset_id for pa in portfolio_assets})
            assets = await self._repo.get_assets_by_ids(asset_ids)

            # Aggregate quantities across portfolios per asset
            qty_by_asset: dict[uuid.UUID, Decimal] = {}
            cost_by_asset: dict[uuid.UUID, Decimal] = {}
            for pa in portfolio_assets:
                qty_by_asset[pa.asset_id] = (
                    qty_by_asset.get(pa.asset_id, Decimal("0")) + pa.quantity
                )
                cost_by_asset[pa.asset_id] = (
                    cost_by_asset.get(pa.asset_id, Decimal("0")) + pa.cost_basis
                )

            for asset_id, qty in qty_by_asset.items():
                asset = assets.get(asset_id)
                if asset is None:
                    continue
                price = asset.current_price or Decimal("0")
                market_value = qty * price
                cost = cost_by_asset.get(asset_id, Decimal("0"))
                total_value += market_value
                total_cost += cost
                asset_type = asset.asset_type
                allocation[asset_type] = allocation.get(asset_type, Decimal("0")) + market_value
                holdings.append(
                    {
                        "asset_id": str(asset_id),
                        "name": asset.name,
                        "symbol": asset.symbol,
                        "asset_type": asset_type,
                        "currency": asset.currency,
                        "quantity": float(qty),
                        "cost_basis": float(cost.quantize(Decimal("0.01"))),
                        "market_value": float(market_value.quantize(Decimal("0.01"))),
                    }
                )

        gain_loss = total_value - total_cost
        percent = (gain_loss / total_cost * 100) if total_cost > 0 else Decimal("0")
        summary = PortfolioSummary(
            total_value=total_value,
            total_cost=total_cost,
            gain_loss=gain_loss,
            gain_loss_percent=percent,
            asset_allocation=allocation,
        )

        logger.info(
            "investment_portfolio_summary",
            user_id=str(user_id),
            portfolios=len(portfolio_ids),
            value=str(total_value),
        )
        return {
            **summary.as_dict(),
            "portfolio_count": len(portfolio_ids),
            "asset_count": len(holdings),
            "holdings": holdings,
        }
