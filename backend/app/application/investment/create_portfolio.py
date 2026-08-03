"""Create a new investment portfolio."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.investment.serializers import serialize_portfolio
from app.infrastructure.repositories.investment_repository import InvestmentRepository
from app.middleware.error_handler import ValidationError

logger = structlog.get_logger()


class CreatePortfolioUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvestmentRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        name: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        if not name or not name.strip():
            raise ValidationError("El nombre del portafolio es requerido")
        if len(name.strip()) > 200:
            raise ValidationError("El nombre no puede exceder 200 caracteres")

        portfolio = await self._repo.create_portfolio(
            user_id=user_id, name=name.strip(), description=description
        )
        logger.info("investment_portfolio_created", portfolio_id=str(portfolio.id))
        return serialize_portfolio(portfolio, asset_count=0)
