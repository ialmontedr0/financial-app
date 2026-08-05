"""Use Case: Escaneo de alertas de tarjetas para cada usuario y espejo de notificaciones."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ScanCardAlertsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(self) -> dict:
        from app.application.cards.check_card_alerts import CheckCardAlertsUseCase

        user_ids = await self._repo.list_active_card_user_ids()
        total_new = 0

        for user_id in user_ids:
            result = await CheckCardAlertsUseCase(self._session).execute(user_id)
            total_new += result["new_alerts"]

        logger.info("card_alerts_scanned", users=len(user_ids), new_alerts=total_new)
        return {"users_scanned": len(user_ids), "new_alerts": total_new}
