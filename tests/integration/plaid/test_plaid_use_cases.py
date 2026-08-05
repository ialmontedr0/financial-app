"""Plaid use cases integration tests (repo real + cliente mockeado)."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.plaid.exchange_public_token import ExchangePublicTokenUseCase
from app.application.plaid.get_transactions import GetPlaidTransactionsUseCase
from app.application.plaid.list_items import ListPlaidItemsUseCase
from app.infrastructure.models.user import UserModel


@pytest.fixture(autouse=True)
def _real_fernet(monkeypatch: pytest.MonkeyPatch) -> None:
    key = Fernet.generate_key()
    monkeypatch.setattr(
        "app.infrastructure.crypto.token_cipher._fernet",
        lambda: Fernet(key),
    )


async def _create_user(session: AsyncSession) -> uuid.UUID:
    user = UserModel(email=f"pl-{uuid.uuid4().hex[:8]}@test.com", password_hash="x")  # noqa: S106
    session.add(user)
    await session.flush()
    return user.id


class FakePlaidClient:
    is_configured = True
    environment = "sandbox"

    def exchange_public_token(self, public_token: str) -> dict:
        return {"access_token": f"access-{public_token}", "item_id": "item-abc-123"}

    def get_item(self, _access_token: str) -> dict:
        return {"item": {"institution_id": "ins_test_1"}}

    def get_institution_name(self, _institution_id: str) -> str:
        return "Test Bank"

    def get_transactions(self, _access_token: str, _start_date: date, _end_date: date) -> dict:
        return {
            "transactions": [
                {
                    "transaction_id": "txn-1",
                    "name": "UBER",
                    "merchant_name": "Uber",
                    "amount": 12.5,
                    "iso_currency_code": "USD",
                    "date": "2026-06-10",
                    "category": ["Travel"],
                    "category_id": "22001000",
                    "account_id": "acc-1",
                    "pending": False,
                    "payment_channel": "online",
                }
            ]
        }

    def remove_item(self, _access_token: str) -> None:
        return None


@pytest.mark.integration
class TestPlaidUseCases:
    async def test_exchange_and_list_item(
        self,
        db_session: AsyncSession,
    ) -> None:
        user_id = await _create_user(db_session)
        client = FakePlaidClient()

        result = await ExchangePublicTokenUseCase(db_session, client).execute(
            user_id=user_id,
            public_token="public-sandbox-fake",  # noqa: S106
        )
        assert result["success"] is True
        item = result["item"]
        assert item["item_id"] == "item-abc-123"
        assert item["institution_name"] == "Test Bank"
        assert item["status"] == "connected"

        listed = await ListPlaidItemsUseCase(db_session).execute(user_id)
        assert len(listed["items"]) == 1
        assert listed["items"][0]["id"] == item["id"]

    async def test_get_transactions(
        self,
        db_session: AsyncSession,
    ) -> None:
        user_id = await _create_user(db_session)
        client = FakePlaidClient()
        exchange = await ExchangePublicTokenUseCase(db_session, client).execute(
            user_id=user_id,
            public_token="public-sandbox-tx",  # noqa: S106
        )
        item_id = uuid.UUID(exchange["item"]["id"])

        result = await GetPlaidTransactionsUseCase(db_session, client).execute(
            user_id=user_id,
            item_id=item_id,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 30),
        )
        assert result["success"] is True
        assert len(result["transactions"]) == 1
        tx = result["transactions"][0]
        assert tx["name"] == "UBER"
        assert tx["amount"] == 12.5
        assert tx["currency_code"] == "USD"
