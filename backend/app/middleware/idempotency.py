"""Middleware de idempotencia con respaldo durable en BD.

Protege los endpoints mutantes (POST/PUT/PATCH) contra duplicados:
si un cliente reenvía el mismo request con la misma cabecera
``Idempotency-Key``, se devuelve la respuesta almacenada en vez de
ejecutar el endpoint de nuevo.

Redis es la caché primaria; la tabla ``idempotency_keys`` en BD actúa
como respaldo durable que sobrevive reinicios de Redis.
"""

from __future__ import annotations

import json

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.infrastructure.cache.redis import redis_client
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.repositories.idempotency_repository import IdempotencyRepository

logger = structlog.get_logger()
settings = get_settings()

IDEMPOTENT_METHODS = {"POST", "PUT", "PATCH"}
IDEMPOTENCY_PREFIX = "fip:idempotency"
STATUS_PENDING = "pending"
STATUS_COMPLETED = "completed"


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Almacena la primera respuesta por clave y reenvía las siguientes.

    - Sin cabecera ``Idempotency-Key``: el request pasa sin cambios.
    - Clave en estado ``completed`` (Redis o BD): se devuelve la respuesta
      cacheada con la cabecera ``Idempotency-Replay: true``.
    - Clave en estado ``pending``: se devuelve 409 (procesamiento en curso).
    - Errores >= 500: se descarta la clave para permitir reintentar.
    """

    def _pending_response(self, idempotency_key: str) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": {
                    "code": "IDEMPOTENCY_PENDING",
                    "message": "A request with this idempotency key is already being processed",
                    "details": [],
                },
            },
            headers={"X-Idempotency-Key": idempotency_key},
        )

    def _replay_response(self, status_code: int, body: str, idempotency_key: str) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content=json.loads(body),
            headers={
                "Idempotency-Replay": "true",
                "X-Idempotency-Key": idempotency_key,
            },
        )

    async def _get_db_record(self, idempotency_key: str):
        async with async_session_factory() as session:  # noqa: SIM117
            async with session.begin():
                return await IdempotencyRepository(session).get(idempotency_key)

    async def _create_db_pending(self, request: Request, idempotency_key: str) -> None:
        async with async_session_factory() as session:  # noqa: SIM117
            async with session.begin():
                await IdempotencyRepository(session).create(
                    key=idempotency_key,
                    method=request.method,
                    path=request.url.path,
                )

    async def _complete_db(self, idempotency_key: str, *, status_code: int, response_body: str) -> None:
        async with async_session_factory() as session:  # noqa: SIM117
            async with session.begin():
                await IdempotencyRepository(session).complete(
                    idempotency_key,
                    status_code=status_code,
                    response_body=response_body,
                )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in IDEMPOTENT_METHODS:
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        redis_key = f"{IDEMPOTENCY_PREFIX}:{idempotency_key}"

        # 1. Caché primaria: Redis
        existing = await redis_client.get(redis_key)
        if existing:
            record = json.loads(existing)
            if record.get("status") == STATUS_COMPLETED:
                return self._replay_response(
                    int(record.get("status_code", 200)),
                    record.get("body", "{}"),
                    idempotency_key,
                )
            return self._pending_response(idempotency_key)

        # 2. Respaldo durable: BD (sobrevive reinicios de Redis)
        db_record = await self._get_db_record(idempotency_key)
        if db_record is not None:
            if db_record.status == STATUS_COMPLETED and db_record.response_body is not None:
                return self._replay_response(
                    db_record.status_code or 200,
                    db_record.response_body,
                    idempotency_key,
                )
            return self._pending_response(idempotency_key)

        # 3. Adquirir el lock en Redis (solo un request procesa cada clave)
        created = await redis_client.set(
            redis_key,
            json.dumps({"status": STATUS_PENDING}),
            nx=True,
            ex=settings.IDEMPOTENCY_KEY_TTL_SECONDS,
        )
        if not created:
            existing = await redis_client.get(redis_key)
            if existing:
                record = json.loads(existing)
                if record.get("status") == STATUS_COMPLETED:
                    return self._replay_response(
                        int(record.get("status_code", 200)),
                        record.get("body", "{}"),
                        idempotency_key,
                    )
            return self._pending_response(idempotency_key)

        # 4. Persistir la clave en estado pending en BD
        await self._create_db_pending(request, idempotency_key)

        try:
            response = await call_next(request)
        except Exception:
            await redis_client.delete(redis_key)
            logger.exception("idempotency_inflight_error", idempotency_key=idempotency_key)
            raise

        if response.status_code < 500:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            body_str = body.decode("utf-8")

            await redis_client.set(
                redis_key,
                json.dumps(
                    {
                        "status": STATUS_COMPLETED,
                        "status_code": response.status_code,
                        "body": body_str,
                    }
                ),
                ex=settings.IDEMPOTENCY_KEY_TTL_SECONDS,
            )
            headers = dict(response.headers)
            headers["Idempotency-Replay"] = "false"
            headers["X-Idempotency-Key"] = idempotency_key
            logger.info(
                "idempotency_completed",
                idempotency_key=idempotency_key,
                status_code=response.status_code,
            )

            await self._complete_db(
                idempotency_key,
                status_code=response.status_code,
                response_body=body_str,
            )

            return Response(
                content=body,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type,
            )

        await redis_client.delete(redis_key)
        return response
