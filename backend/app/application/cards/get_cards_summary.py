"""Use case: Get aggregated card portfolio summary."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetCardsSummaryUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        summary = await self._repo.get_cards_summary(user_id)
        unread = await self._repo.get_unread_alert_count(user_id)
        return {**summary, "unread_alerts": unread}
