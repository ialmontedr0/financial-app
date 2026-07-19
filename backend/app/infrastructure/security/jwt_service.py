import uuid
from datetime import UTC, datetime, timedelta

import structlog
from jose import JWTError, jwt

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class JWTService:
    """Servicio para crear y verificar JWT tokens"""

    @staticmethod
    def create_access_token(
        user_id: str,
        *,
        additional_claims: dict | None = None,
    ) -> str:
        """Crear un un short-lived access token."""
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "type": "access",
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        logger.info("access_token_created", user_id=user_id, expires=expire.isoformat())
        return token

    @staticmethod
    def create_refresh_token(
        user_id: str,
        *,
        additional_claims: dict | None = None,
    ) -> str:
        """Crear un long-lived refresh_token."""
        now = datetime.now(UTC)
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "jti": str(uuid.uuid4()),
            "type": "refresh",
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        logger.info("refresh_token_created", user_id=user_id, expires=expire.isoformat())
        return token

    @staticmethod
    def decode_token(token: str) -> dict | None:
        """Decodificar y validar un token JWT.

        Retorna payload o None en fallo.

        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            return payload
        except JWTError as exc:
            logger.warning("token_decode_failed", error=str(exc))
            return None

    @staticmethod
    def verify_token(token: str, expected_type: str = "access") -> dict | None:
        """Decodifica un token y verifica si el tipo concuerda con el esperado."""
        payload = JWTService.decode_token(token)
        if payload is None:
            return None

        token_type = payload.get("type")
        if token_type != expected_type:
            logger.warning(
                "token_type_mismatch",
                expected=expected_type,
                received=token_type,
            )
            return None

        return payload

    @staticmethod
    def get_token_expiry(token: str) -> datetime | None:
        """Extrae el tiempo de expiracion de un token."""
        payload = JWTService.decode_token(token)
        if payload is None:
            return None
        exp = payload.get("exp")
        if exp is None:
            return None
        return datetime.fromtimestamp(exp, tz=UTC)
