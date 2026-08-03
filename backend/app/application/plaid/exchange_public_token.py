"""Use case: intercambiar public_token por access_token y almacenar el item."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.crypto.token_cipher import encrypt_secret
from app.infrastructure.external.plaid_client import PlaidClient
from app.infrastructure.repositories.plaid_repository import PlaidRepository
from app.middleware.error_handler import ValidationError

logger = structlog.get_logger()


class ExchangePublicTokenUseCase:
    def __init__(self, session: AsyncSession, client: PlaidClient | None = None) -> None:
        self._session = session
        self._repo = PlaidRepository(session)
        self._client = client or PlaidClient()

    async def execute(self, user_id: uuid.UUID, public_token: str) -> dict[str, Any]:
        if not public_token or not public_token.strip():
            raise ValidationError("El public_token es obligatorio")

        if not self._client.is_configured:
            return {"success": False, "enabled": False, "item": None}

        try:
            tokens = await asyncio.to_thread(self._client.exchange_public_token, public_token)
        except Exception as exc:
            logger.error("plaid_exchange_failed", user_id=str(user_id), error=str(exc))
            raise

        access_token = tokens["access_token"]
        plaid_item_id = tokens["item_id"]

        existing = await self._repo.get_item_by_plaid_id(plaid_item_id)
        if existing is not None:
            raise ValidationError("Esta cuenta bancaria ya está vinculada")

        institution_id = None
        institution_name = None
        try:
            item_data = await asyncio.to_thread(self._client.get_item, access_token)
            institution_id = item_data.get("item", {}).get("institution_id")
        except Exception:
            logger.debug("plaid_item_lookup_failed", user_id=str(user_id))
        if institution_id:
            institution_name = await asyncio.to_thread(
                self._client.get_institution_name, institution_id
            )

        item = await self._repo.create_item(
            user_id=user_id,
            item_id=plaid_item_id,
            access_token_encrypted=encrypt_secret(access_token),
            institution_id=institution_id,
            institution_name=institution_name,
            status="connected",
        )

        logger.info(
            "plaid_item_linked",
            user_id=str(user_id),
            item_id=str(item.id),
            institution=institution_name,
        )
        return {
            "success": True,
            "enabled": True,
            "item": {
                "id": str(item.id),
                "item_id": item.item_id,
                "institution_id": item.institution_id,
                "institution_name": item.institution_name,
                "status": item.status,
                "last_sync_at": item.last_sync_at.isoformat() if item.last_sync_at else None,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            },
        }
