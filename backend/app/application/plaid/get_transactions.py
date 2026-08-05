"""Use case: obtener transacciones de un item Plaid."""

from __future__ import annotations

import asyncio
import uuid
from datetime import date
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.crypto.token_cipher import decrypt_secret
from app.infrastructure.external.plaid_client import PlaidClient
from app.infrastructure.repositories.plaid_repository import PlaidRepository
from app.middleware.error_handler import NotFoundError, ValidationError

logger = structlog.get_logger()


class GetPlaidTransactionsUseCase:
    def __init__(self, session: AsyncSession, client: PlaidClient | None = None) -> None:
        self._session = session
        self._repo = PlaidRepository(session)
        self._client = client or PlaidClient()

    async def execute(
        self,
        user_id: uuid.UUID,
        item_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        if start_date > end_date:
            raise ValidationError("start_date no puede ser posterior a end_date")

        item = await self._repo.get_item(item_id, user_id)
        if item is None:
            raise NotFoundError("Item de Plaid no encontrado")

        if not self._client.is_configured:
            return {"success": False, "enabled": False, "transactions": []}

        access_token = decrypt_secret(item.access_token_encrypted)

        try:
            data = await asyncio.to_thread(
                self._client.get_transactions, access_token, start_date, end_date
            )
        except Exception as exc:
            logger.error("plaid_transactions_failed", user_id=str(user_id), error=str(exc))
            raise

        await self._repo.touch_sync(item)

        return {
            "success": True,
            "enabled": True,
            "account_id": item.id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "transactions": [self._map_transaction(tx) for tx in data.get("transactions", [])],
        }

    @staticmethod
    def _map_transaction(tx: dict[str, Any]) -> dict[str, Any]:
        amount_value = tx.get("amount")
        amount = abs(Decimal(str(amount_value))) if amount_value is not None else None
        return {
            "transaction_id": tx.get("transaction_id"),
            "name": tx.get("name"),
            "merchant_name": tx.get("merchant_name"),
            "amount": float(amount) if amount is not None else None,
            "amount_decimal": str(amount) if amount is not None else None,
            "currency_code": tx.get("iso_currency_code") or tx.get("unofficial_currency_code"),
            "date": tx.get("date"),
            "datetime": tx.get("datetime"),
            "category": (tx.get("category") or [None])[0],
            "category_id": tx.get("category_id"),
            "account_id": tx.get("account_id"),
            "pending": bool(tx.get("pending", False)),
            "payment_channel": tx.get("payment_channel"),
            "logo_url": tx.get("logo_url"),
        }
