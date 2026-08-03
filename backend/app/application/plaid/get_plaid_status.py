"""Use case: estado de la integracion Plaid."""

from __future__ import annotations

from typing import Any

from app.infrastructure.external.plaid_client import PlaidClient


class GetPlaidStatusUseCase:
    def __init__(self, client: PlaidClient | None = None) -> None:
        self._client = client or PlaidClient()

    def execute(self) -> dict[str, Any]:
        return {
            "enabled": self._client.is_configured,
            "environment": self._client.environment,
        }
