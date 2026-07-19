"""Use case: Get a single financial account."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.account_repository import AccountRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetAccountUseCase:
    """Get a single financial account by ID."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AccountRepository(session)

    async def execute(self, user_id: uuid.UUID, account_id: uuid.UUID) -> dict:
        """Return a single account."""
        from app.middleware.error_handler import NotFoundError

        account = await self._repo.get_by_id(account_id, user_id)
        if account is None:
            raise NotFoundError("Account")

        return {
            "id": str(account.id),
            "name": account.name,
            "account_type": account.account_type,
            "status": account.status,
            "currency_code": account.currency_code,
            "balance": str(account.balance),
            "initial_balance": str(account.initial_balance),
            "institution": account.institution,
            "account_number_last4": account.account_number_last4,
            "icon": account.icon,
            "color": account.color,
            "notes": account.notes,
            "include_in_net_worth": account.include_in_net_worth,
            "include_in_totals": account.include_in_totals,
            "sort_order": account.sort_order,
            "created_at": account.created_at.isoformat() if account.created_at else None,
            "updated_at": account.updated_at.isoformat() if account.updated_at else None,
        }
