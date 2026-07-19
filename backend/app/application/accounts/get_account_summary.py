"""Use case: Get aggregated account summary."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.account_repository import AccountRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetAccountSummaryUseCase:
    """Get aggregated financial account summary."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AccountRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        """Return account summary with totals by currency."""
        summary = await self._repo.get_summary(user_id)
        return summary
