"""List investment portfolios for the current user."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.investment.serializers import serialize_portfolio
from app.infrastructure.repositories.investment_repository import InvestmentRepository

logger = structlog.get_logger()


class ListPortfoliosUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvestmentRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict[str, Any]:
        portfolios = await self._repo.list_portfolios(user_id)
        portfolio_ids = [p.id for p in portfolios]
        counts: dict[uuid.UUID, int] = {}
        if portfolio_ids:
            portfolio_assets = await self._repo.list_assets_in_portfolios(portfolio_ids)
            for pa in portfolio_assets:
                counts[pa.portfolio_id] = counts.get(pa.portfolio_id, 0) + 1

        result = [
            serialize_portfolio(p, asset_count=counts.get(p.id, 0)) for p in portfolios
        ]
        logger.info("investment_portfolios_listed", user_id=str(user_id), count=len(result))
        return {"portfolios": result, "total": len(result)}
