"""Use case: Get a single wallet."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.wallet_repository import WalletRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetWalletUseCase:
    """Get a single wallet by ID with account list."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = WalletRepository(session)

    async def execute(self, user_id: uuid.UUID, wallet_id: uuid.UUID) -> dict:
        """Return a single wallet with linked accounts."""
        from app.middleware.error_handler import NotFoundError

        wallet = await self._repo.get_by_id(wallet_id, user_id)
        if wallet is None:
            raise NotFoundError("Wallet")

        account_ids = await self._repo.get_wallet_account_ids(wallet_id)
        accounts: list[dict] = []
        if account_ids:
            from sqlalchemy import select

            from app.infrastructure.models.financial_account import FinancialAccountModel

            stmt = select(FinancialAccountModel).where(
                FinancialAccountModel.id.in_(account_ids),
                FinancialAccountModel.deleted_at.is_(None),
            )
            result = await self._session.execute(stmt)
            for a in result.scalars().all():
                accounts.append({
                    "id": str(a.id),
                    "name": a.name,
                    "account_type": a.account_type,
                    "currency_code": a.currency_code,
                    "balance": str(a.balance),
                    "status": a.status,
                })

        return {
            "id": str(wallet.id),
            "name": wallet.name,
            "description": wallet.description,
            "wallet_type": wallet.wallet_type,
            "status": wallet.status,
            "icon": wallet.icon,
            "color": wallet.color,
            "sort_order": wallet.sort_order,
            "accounts": accounts,
            "created_at": wallet.created_at.isoformat() if wallet.created_at else None,
            "updated_at": wallet.updated_at.isoformat() if wallet.updated_at else None,
        }
