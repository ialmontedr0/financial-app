"""Use case: Get wallet liquidity analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.wallet_repository import WalletRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetWalletLiquidityUseCase:
    """Get liquidity analysis for a wallet based on account types."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = WalletRepository(session)

    async def execute(self, user_id: uuid.UUID, wallet_id: uuid.UUID) -> dict:
        """Return liquidity breakdown."""
        from app.middleware.error_handler import NotFoundError

        wallet = await self._repo.get_by_id(wallet_id, user_id)
        if wallet is None:
            raise NotFoundError("Wallet")

        liquidity = await self._repo.get_wallet_liquidity(wallet_id, user_id)

        return {
            "wallet_id": str(wallet_id),
            "wallet_name": wallet.name,
            **liquidity,
        }
