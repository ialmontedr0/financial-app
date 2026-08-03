"""Middleware de conversion automatica de divisas.

Cuando un cliente lista recursos financieros (transacciones, ingresos,
gastos, cuentas) y envía la cabecera ``X-Currency``, este middleware
convierte los montos de la divisa nativa de cada item a la divisa pedida
usando las tasas de cambio cacheadas (con fallback a la API externa).

El middleware es "best-effort": ante cualquier error de parseo o tasa
desconocida, la respuesta se devuelve sin convertir para no romper la
experiencia del usuario.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import date
from decimal import Decimal
from typing import Any

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.api.deps import get_db
from app.core.config import get_settings
from app.middleware.error_handler import CurrencyConversionError

logger = structlog.get_logger()
settings = get_settings()

CONVERTIBLE_PREFIXES = (
    "/api/v1/transactions",
    "/api/v1/incomes",
    "/api/v1/expenses",
    "/api/v1/accounts",
)

# Campo numerico convertido por tipo de colección.
_AMOUNT_FIELD_BY_COLLECTION: dict[str, str] = {
    "transactions": "amount",
    "incomes": "amount",
    "expenses": "amount",
    "accounts": "balance",
}


class CurrencyConversionMiddleware(BaseHTTPMiddleware):
    """Convierte montos en listados GET según la cabecera ``X-Currency``."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not settings.AUTO_CURRENCY_CONVERSION:
            return await call_next(request)

        if request.method != "GET":
            return await call_next(request)

        target = request.headers.get("X-Currency", "").strip().upper()
        path = request.url.path
        collection = self._match_collection(path)
        if not collection or not target:
            return await call_next(request)

        from app.domain.users.value_objects import CurrencyCode

        try:
            target = CurrencyCode(target).code
        except ValueError:
            return await call_next(request)

        try:
            response = await call_next(request)
            return await self._convert_response(request, response, collection, target)
        except Exception:  # never break the request
            logger.exception(
                "currency_conversion_error",
                path=path,
                target_currency=target,
            )
            return await call_next(request)

    @staticmethod
    def _match_collection(path: str) -> str | None:
        """Devuelve el nombre de la coleccion a convertir o None."""
        for prefix, name in (
            ("/api/v1/transactions", "transactions"),
            ("/api/v1/incomes", "incomes"),
            ("/api/v1/expenses", "expenses"),
            ("/api/v1/accounts", "accounts"),
        ):
            if path == prefix:
                return name
        return None

    @staticmethod
    async def _iter_db_session(request: Request) -> AsyncIterator[Any]:
        """Resuelve la sesion de DB respetando dependency_overrides (tests).

        Permite que los tests reemplacen ``get_db`` por una sesion apuntando
        a la base de datos de prueba, igual que hacen los routers.
        """
        dependency = request.app.dependency_overrides.get(get_db) or get_db
        async for session in dependency():
            yield session

    async def _convert_response(
        self,
        request: Request,
        response: Response,
        collection: str,
        target: str,
    ) -> Response:
        body = b""
        async for chunk in response.body_iterator:  # type: ignore[attr-defined]
            body += chunk

        if response.status_code != 200 or not body:
            return self._rebuild(response, body)

        try:
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._rebuild(response, body)

        items = data.get(collection) if isinstance(data, dict) else data
        if not isinstance(items, list) or not items:
            return self._rebuild(response, body)

        amount_field = _AMOUNT_FIELD_BY_COLLECTION[collection]
        from_currencies: set[str] = {
            str(item.get("currency_code", "")).upper() for item in items if isinstance(item, dict)
        }
        if not from_currencies:
            return self._rebuild(response, body)

        rates: dict[str, Decimal | None] = {}
        converted_any = False

        async for session in self._iter_db_session(request):
            from app.application.currency.convert_currency import ConvertCurrencyUseCase

            use_case = ConvertCurrencyUseCase(session)
            today = date.today()  # noqa: DTZ011
            for source in sorted(from_currencies):
                if source == target:
                    rates[source] = Decimal("1")
                    continue
                try:
                    result = await use_case.execute(1, source, target, today)
                    rates[source] = Decimal(result["rate"])
                except CurrencyConversionError as exc:
                    logger.warning(
                        "currency_conversion_skipped", source=source, target=target, error=str(exc)
                    )
                    rates[source] = None

        for item in items:
            if not isinstance(item, dict):
                continue
            source = str(item.get("currency_code", "")).upper()
            rate = rates.get(source)
            if rate is None or source == target:
                continue
            raw_amount = item.get(amount_field)
            if raw_amount is None:
                continue
            try:
                value = Decimal(str(raw_amount))
                converted = (value * rate).quantize(Decimal("0.0001"))
            except (ValueError, ArithmeticError):
                continue
            item[amount_field] = str(converted)
            item["original_currency"] = source
            converted_any = True

        if not converted_any:
            return self._rebuild(response, body)

        headers = dict(response.headers)
        headers["X-Converted"] = f"{','.join(sorted(from_currencies))}->{target}"
        return JSONResponse(
            status_code=response.status_code,
            content=data,
            headers=headers,
        )

    @staticmethod
    def _rebuild(response: Response, body: bytes) -> Response:
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
