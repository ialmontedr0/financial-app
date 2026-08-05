"""Use case: desvincular un item Plaid."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.crypto.token_cipher import decrypt_secret
from app.infrastructure.external.plaid_client import PlaidClient, PlaidNotConfiguredError
from app.infrastructure.repositories.plaid_repository import PlaidRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class DeletePlaidItemUseCase:
    def __init__(self, session: AsyncSession, client: PlaidClient | None = None) -> None:
        self._session = session
        self._repo = PlaidRepository(session)
        self._client = client or PlaidClient()

    async def execute(self, user_id: uuid.UUID, item_id: uuid.UUID) -> dict[str, Any]:
        item = await self._repo.get_item(item_id, user_id)
        if item is None:
            raise NotFoundError("Item de Plaid no encontrado")

        if self._client.is_configured:
            try:
                access_token = decrypt_secret(item.access_token_encrypted)
                await asyncio.to_thread(self._client.remove_item, access_token)
            except PlaidNotConfiguredError:
                pass
            except Exception as exc:
                logger.warning("plaid_remote_remove_failed", user_id=str(user_id), error=str(exc))

        await self._repo.delete_item(item)
        logger.info("plaid_item_unlinked", user_id=str(user_id), item_id=str(item.id))
        return {"success": True, "id": str(item.id)}
