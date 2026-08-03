"""Use case: listar items Plaid vinculados al usuario."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.plaid_repository import PlaidRepository

logger = structlog.get_logger()


class ListPlaidItemsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = PlaidRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict[str, Any]:
        items = await self._repo.list_items(user_id)
        return {
            "items": [
                {
                    "id": str(item.id),
                    "item_id": item.item_id,
                    "institution_id": item.institution_id,
                    "institution_name": item.institution_name,
                    "status": item.status,
                    "last_sync_at": item.last_sync_at.isoformat() if item.last_sync_at else None,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in items
            ]
        }
