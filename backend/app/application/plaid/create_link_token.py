"""Use case: crear un link token de Plaid Link."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import structlog

from app.infrastructure.external.plaid_client import PlaidClient, PlaidNotConfiguredError

logger = structlog.get_logger()


class CreateLinkTokenUseCase:
    def __init__(self, client: PlaidClient | None = None) -> None:
        self._client = client or PlaidClient()

    async def execute(self, user_id: uuid.UUID, redirect_uri: str | None = None) -> dict[str, Any]:
        try:
            link_token = await asyncio.to_thread(
                self._client.create_link_token, user_id, redirect_uri
            )
        except PlaidNotConfiguredError:
            return {"success": False, "enabled": False, "link_token": None}
        except Exception as exc:
            logger.error("plaid_link_token_failed", user_id=str(user_id), error=str(exc))
            raise

        return {"success": True, "enabled": True, "link_token": link_token}
