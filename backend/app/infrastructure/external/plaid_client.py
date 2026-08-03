"""Cliente Plaid (plaid-python) con degradacion controlada.

Si no hay credenciales o PLAID_ENABLED=False, los metodos lanzan
PlaidNotConfiguredError; los use cases traducen eso a respuestas
`enabled: False` en lugar de fallar.
"""

from __future__ import annotations

import uuid
from datetime import date

import structlog

from app.core.config import get_settings

logger = structlog.get_logger()


class PlaidNotConfiguredError(Exception):
    """Plaid no esta configurado (sin credenciales o deshabilitado)."""


_HOSTS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com",
}

_PLAID_VERSION = "2020-09-14"


class PlaidClient:
    """Wrapper ligero sobre el SDK oficial de Plaid (importacion lazy)."""

    def __init__(self, settings=None) -> None:
        from app.core.config import Settings

        self._settings: Settings = settings or get_settings()

    @property
    def is_configured(self) -> bool:
        settings = self._settings
        return bool(settings.PLAID_ENABLED and settings.PLAID_CLIENT_ID and settings.PLAID_SECRET)

    @property
    def environment(self) -> str:
        env = self._settings.PLAID_ENVIRONMENT
        if env not in _HOSTS:
            env = "sandbox"
        return env

    def _ensure_configured(self) -> None:
        if not self.is_configured:
            raise PlaidNotConfiguredError(
                "Plaid no configurado. Configura PLAID_CLIENT_ID y PLAID_SECRET."
            )

    def _api(self):
        # Importacion lazy para permitir arranque sin el SDK instalado.
        from plaid.api import plaid_api
        from plaid.api_client import ApiClient, Configuration

        host = _HOSTS.get(self.environment, _HOSTS["sandbox"])
        configuration = Configuration(host=host)
        configuration.api_key["clientId"] = self._settings.PLAID_CLIENT_ID
        configuration.api_key["secret"] = self._settings.PLAID_SECRET
        configuration.api_key["plaidVersion"] = _PLAID_VERSION
        return plaid_api.PlaidApi(ApiClient(configuration))

    def create_link_token(self, user_id: uuid.UUID, redirect_uri: str | None = None) -> str:
        self._ensure_configured()
        from plaid.model.country_code import CountryCode
        from plaid.model.link_token_create_request import LinkTokenCreateRequest
        from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
        from plaid.model.products import Products

        request = LinkTokenCreateRequest(
            client_name="FIP",
            country_codes=[CountryCode("US"), CountryCode("MX")],
            language="es",
            user=LinkTokenCreateRequestUser(client_user_id=str(user_id)),
            products=[Products("transactions")],
            redirect_uri=redirect_uri or None,
        )
        response = self._api().link_token_create(request)
        return response.link_token

    def exchange_public_token(self, public_token: str) -> dict:
        self._ensure_configured()
        from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self._api().item_public_token_exchange(request)
        data = response.to_dict()
        return {
            "access_token": data["access_token"],
            "item_id": data["item_id"],
        }

    def get_item(self, access_token: str) -> dict:
        self._ensure_configured()
        from plaid.model.item_get_request import ItemGetRequest

        request = ItemGetRequest(access_token=access_token)
        response = self._api().item_get(request)
        return response.to_dict()

    def get_institution_name(self, institution_id: str) -> str | None:
        self._ensure_configured()
        try:
            from plaid.model.country_code import CountryCode
            from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest

            request = InstitutionsGetByIdRequest(
                institution_id=institution_id,
                country_codes=[CountryCode("US"), CountryCode("MX")],
            )
            response = self._api().institutions_get_by_id(request)
            return response.to_dict()["institution"].get("name")
        except Exception as exc:
            logger.debug("plaid_institution_lookup_failed", error=str(exc))
            return None

    def get_transactions(self, access_token: str, start_date: date, end_date: date) -> dict:
        self._ensure_configured()
        from plaid.model.transactions_get_request import TransactionsGetRequest
        from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions

        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            options=TransactionsGetRequestOptions(count=500),
        )
        response = self._api().transactions_get(request)
        return response.to_dict()

    def remove_item(self, access_token: str) -> None:
        self._ensure_configured()
        from plaid.model.item_remove_request import ItemRemoveRequest

        request = ItemRemoveRequest(access_token=access_token)
        self._api().item_remove(request)
