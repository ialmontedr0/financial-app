"""Delete an investment portfolio (soft delete)."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.investment_repository import InvestmentRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class DeletePortfolioUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvestmentRepository(session)

    async def execute(self, user_id: uuid.UUID, portfolio_id: uuid.UUID) -> dict[str, Any]:
        portfolio = await self._repo.get_portfolio(portfolio_id, user_id)
        if portfolio is None:
            raise NotFoundError("Portafolio")
        await self._repo.delete_portfolio(portfolio)
        logger.info("investment_portfolio_deleted", portfolio_id=str(portfolio_id))
        return {"id": str(portfolio_id), "status": "deleted"}
