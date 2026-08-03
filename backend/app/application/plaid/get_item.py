"""Use case: obtener un item Plaid del usuario."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.plaid_repository import PlaidRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class GetPlaidItemUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = PlaidRepository(session)

    async def execute(self, user_id: uuid.UUID, item_id: uuid.UUID) -> dict[str, Any]:
        item = await self._repo.get_item(item_id, user_id)
        if item is None:
            raise NotFoundError("Item de Plaid no encontrado")
        return {
            "id": str(item.id),
            "item_id": item.item_id,
            "institution_id": item.institution_id,
            "institution_name": item.institution_name,
            "status": item.status,
            "last_sync_at": item.last_sync_at.isoformat() if item.last_sync_at else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
