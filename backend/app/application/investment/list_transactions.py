"""List investment transactions for an asset or a portfolio."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.investment.serializers import serialize_transaction
from app.infrastructure.repositories.investment_repository import InvestmentRepository

logger = structlog.get_logger()


class ListTransactionsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvestmentRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        asset_id: uuid.UUID | None = None,
        portfolio_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        if portfolio_id is not None:
            transactions = await self._repo.list_portfolio_transactions(portfolio_id)
        elif asset_id is not None:
            transactions = await self._repo.list_asset_transactions(asset_id)
        else:
            transactions = await self._repo.list_user_transactions(user_id)

        logger.info("investment_transactions_listed", user_id=str(user_id), count=len(transactions))
        return {"transactions": [serialize_transaction(tx) for tx in transactions], "total": len(transactions)}
