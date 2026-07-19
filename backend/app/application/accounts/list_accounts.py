"""Use case: List financial accounts."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.account_repository import AccountRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListAccountsUseCase:
    """List all financial accounts for the authenticated user."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AccountRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        account_type: str | None = None,
        include_archived: bool = False,
    ) -> list[dict]:
        """Return list of accounts."""
        accounts = await self._repo.list_by_user(
            user_id,
            account_type=account_type,
            include_archived=include_archived,
        )

        return [
            {
                "id": str(a.id),
                "name": a.name,
                "account_type": a.account_type,
                "status": a.status,
                "currency_code": a.currency_code,
                "balance": str(a.balance),
                "institution": a.institution,
                "icon": a.icon,
                "color": a.color,
                "include_in_net_worth": a.include_in_net_worth,
                "sort_order": a.sort_order,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in accounts
        ]
