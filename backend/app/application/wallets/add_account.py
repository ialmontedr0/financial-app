"""Use case: Add an account to a wallet."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.wallet_repository import WalletRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class AddAccountToWalletUseCase:
    """Link a financial account to a wallet."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = WalletRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        wallet_id: uuid.UUID,
        account_id: uuid.UUID,
        notes: str | None = None,
    ) -> dict:
        """Add account to wallet."""
        from app.middleware.error_handler import NotFoundError, ValidationError

        wallet = await self._repo.get_by_id(wallet_id, user_id)
        if wallet is None:
            raise NotFoundError("Wallet")

        wa = await self._repo.add_account(wallet_id, account_id, user_id, notes=notes)
        if wa is None:
            raise ValidationError("Cuenta no encontrada o no pertenece al usuario")

        return {
            "message": "Cuenta agregada a la wallet exitosamente",
            "wallet_id": str(wallet_id),
            "account_id": str(account_id),
            "added_at": wa.added_at.isoformat() if wa.added_at else None,
        }
