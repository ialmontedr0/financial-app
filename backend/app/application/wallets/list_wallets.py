"""Use case: List wallets."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.wallet_repository import WalletRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListWalletsUseCase:
    """List all wallets for the authenticated user."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = WalletRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        wallet_type: str | None = None,
    ) -> list[dict]:
        """Return list of wallets."""
        wallets = await self._repo.list_by_user(user_id, wallet_type=wallet_type)

        result: list[dict] = []
        for w in wallets:
            account_ids = await self._repo.get_wallet_account_ids(w.id)
            result.append({
                "id": str(w.id),
                "name": w.name,
                "description": w.description,
                "wallet_type": w.wallet_type,
                "status": w.status,
                "icon": w.icon,
                "color": w.color,
                "sort_order": w.sort_order,
                "account_count": len(account_ids),
                "created_at": w.created_at.isoformat() if w.created_at else None,
            })

        return result
