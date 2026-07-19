"""Use case: Remove an account from a wallet."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.wallet_repository import WalletRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class RemoveAccountFromWalletUseCase:
    """Unlink a financial account from a wallet."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = WalletRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        wallet_id: uuid.UUID,
        account_id: uuid.UUID,
    ) -> dict:
        """Remove account from wallet."""
        from app.middleware.error_handler import NotFoundError

        wallet = await self._repo.get_by_id(wallet_id, user_id)
        if wallet is None:
            raise NotFoundError("Wallet")

        removed = await self._repo.remove_account(wallet_id, account_id)
        if not removed:
            raise NotFoundError("WalletAccount association")

        logger.info(
            "wallet_account_removed",
            user_id=str(user_id),
            wallet_id=str(wallet_id),
            account_id=str(account_id),
        )

        return {
            "message": "Cuenta removida de la wallet exitosamente",
            "wallet_id": str(wallet_id),
            "account_id": str(account_id),
        }
