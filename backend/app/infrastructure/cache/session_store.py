import json
from datetime import UTC, datetime

import structlog

from app.core.config import get_settings
from app.infrastructure.cache.redis import redis_client

logger = structlog.get_logger()
settings = get_settings()

# Redis key prefixes
SESSION_PREFIX = "fip:session"
REFRESH_PREFIX = "fip:refresh"
EMAIL_VERIFICATION_PREFIX = "fip:email_verification"


class SessionStore:
    """Manejo de Redis-backed session y token."""

    # ---- Manejo de Sesion ----
    @staticmethod
    async def create_session(
        jti: str,
        user_id: str,
        device_info: str,
        ip_address: str,
        ttl_seconds: int | None = None,
    ) -> None:
        """Almacena una nueva sesion en Redis."""
        if ttl_seconds is None:
            ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

        key = f"{SESSION_PREFIX}:{jti}"
        data = {
            "user_id": user_id,
            "jti": jti,
            "device_info": device_info,
            "ip_address": ip_address,
            "created_at": datetime.now(UTC).isoformat(),
            "is_active": True,
        }
        await redis_client.setex(key, ttl_seconds, json.dumps(data))
        user_sessions_key = f"{SESSION_PREFIX}:user:{user_id}"
        await redis_client.sadd(user_sessions_key, key)
        await redis_client.expire(user_sessions_key, ttl_seconds)

        logger.info("session_created", jti=jti, user_id=user_id)

    @staticmethod
    async def get_session(jti: str) -> dict | None:
        """Obtiene una sesion desde Redis."""
        key = f"{SESSION_PREFIX}:{jti}"
        raw = await redis_client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    @staticmethod
    async def delete_session(jti: str) -> None:
        """Elimina una sesion desde Redis."""
        key = f"{SESSION_PREFIX}:{jti}"
        raw = await redis_client.get(key)
        if raw:
            data = json.loads(raw)
            uid = data.get("user_id")
            if uid:
                await redis_client.srem(f"{SESSION_PREFIX}:user:{uid}", key)
        await redis_client.delete(key)

    @staticmethod
    async def revoke_all_user_sessions(
        user_id: str,
    ) -> int:
        """Revoca todas las sessiones de un usuario dado.

        Retorna el numero de sesiones revocadas.
        """
        user_sessions_key = f"{SESSION_PREFIX}:user:{user_id}"
        keys = await redis_client.smembers(user_sessions_key)
        if keys:
            await redis_client.delete(*keys)
            await redis_client.delete(user_sessions_key)
        count = len(keys)
        logger.info("all_sessions_revoked", user_id=user_id, count=count)
        return count

    @staticmethod
    async def get_user_sessions(user_id: str) -> list[dict]:
        """Obtiene todas las sesiones activas para un usuario."""
        user_sessions_key = f"{SESSION_PREFIX}:user:{user_id}"
        keys = await redis_client.smembers(user_sessions_key)
        sessions = []
        for key in keys:
            raw = await redis_client.get(key)
            if raw:
                data = json.loads(raw)
                if data.get("is_active"):
                    sessions.append(data)
        return sessions

    # ---- Manejo de Refresh Token ----
    @staticmethod
    async def store_refresh_token(
        jti: str,
        user_id: str,
        ttl_seconds: int | None = None,
    ) -> None:
        """Almacena token refresh JTI en Redis para validacion."""
        if ttl_seconds is None:
            ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

        key = f"{REFRESH_PREFIX}:{jti}"
        await redis_client.setex(key, ttl_seconds, user_id)

    @staticmethod
    async def get_refresh_token(jti: str) -> str | None:
        """Obtiene el user_id asociado a un refresh token JTI."""
        key = f"{REFRESH_PREFIX}:{jti}"
        return await redis_client.get(key)

    @staticmethod
    async def consume_refresh_token(jti: str) -> str | None:
        """Consume el refresh token de forma atómica (get + delete).

        El get-and-delete se ejecuta en un script Lua, por lo que dos peticiones
        de refresh concurrentes con el mismo JTI no pueden ganar ambas: solo una
        recibe el valor y la otra obtiene None (detección de reuso).
        """
        key = f"{REFRESH_PREFIX}:{jti}"
        script = """
        local value = redis.call('GET', KEYS[1])
        if value then
            redis.call('DEL', KEYS[1])
        end
        return value
        """
        return await redis_client.eval(script, 1, key)

    @staticmethod
    async def delete_refresh_token(jti: str) -> None:
        """Delete a refresh token from Redis (invalidation)."""
        key = f"{REFRESH_PREFIX}:{jti}"
        await redis_client.delete(key)

    # ---- Email Verification Tokens ----

    @staticmethod
    async def store_email_verification(
        token: str,
        user_id: str,
        purpose: str,
        ttl_seconds: int = 86400,
    ) -> None:
        """Store an email verification token."""
        key = f"{EMAIL_VERIFICATION_PREFIX}:{token}"
        data = {"user_id": user_id, "purpose": purpose}
        await redis_client.setex(key, ttl_seconds, json.dumps(data))

    @staticmethod
    async def get_email_verification(token: str) -> dict | None:
        """Get email verification data."""
        key = f"{EMAIL_VERIFICATION_PREFIX}:{token}"
        raw = await redis_client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    @staticmethod
    async def delete_email_verification(token: str) -> None:
        """Delete an email verification token (after use)."""
        key = f"{EMAIL_VERIFICATION_PREFIX}:{token}"
        await redis_client.delete(key)
