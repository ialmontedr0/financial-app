"""Servicio de blacklist de tokens JWT basado en Redis.

Permite revocar un access token de forma inmediata (logout) y validar
en cada request autenticado que el ``jti`` del token no haya sido
revocado. El TTL de cada entrada equivale a la vida restante del token.
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog

from app.infrastructure.cache.redis import redis_client
from app.infrastructure.security.jwt_service import JWTService

logger = structlog.get_logger()

ACCESS_BLACKLIST_PREFIX = "fip:blacklist:access"
REFRESH_BLACKLIST_PREFIX = "fip:blacklist:refresh"


class TokenBlacklistService:
    """Manejo de tokens revocados en Redis."""

    @staticmethod
    def _prefix_for(kind: str) -> str:
        if kind == "refresh":
            return REFRESH_BLACKLIST_PREFIX
        return ACCESS_BLACKLIST_PREFIX

    @classmethod
    async def blacklist_token(cls, token: str) -> bool:
        """Revoca un token usando su ``jti`` y tiempo de expiración.

        Devuelve ``True`` si el token fue agregado a la blacklist.
        """
        payload = JWTService.decode_token(token)
        if payload is None:
            return False
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or exp is None:
            return False
        ttl = int(exp - datetime.now(UTC).timestamp())
        if ttl <= 0:
            return False
        key = f"{cls._prefix_for(payload.get('type', 'access'))}:{jti}"
        await redis_client.setex(key, ttl, "1")
        logger.info("token_blacklisted", jti=jti, kind=payload.get("type"), ttl=ttl)
        return True

    @staticmethod
    async def is_blacklisted(jti: str, kind: str = "access") -> bool:
        """Comprueba si el ``jti`` está revocado para un tipo de token."""
        key = f"{TokenBlacklistService._prefix_for(kind)}:{jti}"
        return await redis_client.exists(key) > 0

    @staticmethod
    async def blacklist_access_jti(jti: str, exp: int) -> bool:
        """Revoca un access token a partir de su ``jti`` y expiración (unix)."""
        ttl = int(exp - datetime.now(UTC).timestamp())
        if ttl <= 0:
            return False
        await redis_client.setex(f"{ACCESS_BLACKLIST_PREFIX}:{jti}", ttl, "1")
        logger.info("access_token_blacklisted", jti=jti, ttl=ttl)
        return True
