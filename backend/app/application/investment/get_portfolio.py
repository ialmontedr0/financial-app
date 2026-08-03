"""Get a single investment portfolio with its assets and transactions."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.investment.serializers import (
    serialize_portfolio,
    serialize_portfolio_asset,
    serialize_transaction,
)
from app.infrastructure.repositories.investment_repository import InvestmentRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class GetPortfolioUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvestmentRepository(session)

    async def execute(self, user_id: uuid.UUID, portfolio_id: uuid.UUID) -> dict[str, Any]:
        portfolio = await self._repo.get_portfolio(portfolio_id, user_id)
        if portfolio is None:
            raise NotFoundError("Portafolio")

        portfolio_assets = await self._repo.list_portfolio_assets(portfolio_id)
        asset_ids = [pa.asset_id for pa in portfolio_assets]
        assets = await self._repo.get_assets_by_ids(asset_ids) if asset_ids else {}
        transactions = await self._repo.list_portfolio_transactions(portfolio_id)

        logger.info("investment_portfolio_retrieved", portfolio_id=str(portfolio_id))
        return {
            **serialize_portfolio(portfolio, asset_count=len(portfolio_assets)),
            "assets": [
                serialize_portfolio_asset(pa, assets.get(pa.asset_id)) for pa in portfolio_assets
            ],
            "transactions": [serialize_transaction(tx) for tx in transactions],
        }
