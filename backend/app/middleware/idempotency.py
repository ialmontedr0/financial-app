"""Middleware de idempotencia basado en Redis.

Protege los endpoints mutantes (POST/PUT/PATCH) contra duplicados:
si un cliente reenvía el mismo request con la misma cabecera
``Idempotency-Key``, se devuelve la respuesta almacenada en vez de
ejecutar el endpoint de nuevo.
"""

from __future__ import annotations

import json

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.infrastructure.cache.redis import redis_client

logger = structlog.get_logger()
settings = get_settings()

IDEMPOTENT_METHODS = {"POST", "PUT", "PATCH"}
IDEMPOTENCY_PREFIX = "fip:idempotency"
STATUS_PENDING = "pending"
STATUS_COMPLETED = "completed"


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Almacena la primera respuesta por clave y reenvía las siguientes.

    - Sin cabecera ``Idempotency-Key``: el request pasa sin cambios.
    - Clave en estado ``completed``: se devuelve la respuesta cacheada con
      la cabecera ``Idempotency-Replay: true``.
    - Clave en estado ``pending``: se devuelve 409 (procesamiento en curso).
    - Errores >= 500: se descarta la clave para permitir reintentar.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in IDEMPOTENT_METHODS:
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        redis_key = f"{IDEMPOTENCY_PREFIX}:{idempotency_key}"
        existing = await redis_client.get(redis_key)
        if existing:
            record = json.loads(existing)
            if record.get("status") == STATUS_COMPLETED:
                return JSONResponse(
                    status_code=int(record.get("status_code", 200)),
                    content=json.loads(record.get("body", "{}")),
                    headers={
                        "Idempotency-Replay": "true",
                        "X-Idempotency-Key": idempotency_key,
                    },
                )
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
                    return JSONResponse(
                        status_code=int(record.get("status_code", 200)),
                        content=json.loads(record.get("body", "{}")),
                        headers={
                            "Idempotency-Replay": "true",
                            "X-Idempotency-Key": idempotency_key,
                        },
                    )
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
            await redis_client.set(
                redis_key,
                json.dumps(
                    {
                        "status": STATUS_COMPLETED,
                        "status_code": response.status_code,
                        "body": body.decode("utf-8"),
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
            return Response(
                content=body,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type,
            )

        await redis_client.delete(redis_key)
        return response
