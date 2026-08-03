"""Servicio de lockout por intentos fallidos de login."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.infrastructure.models.login_attempt import LoginAttemptModel

logger = structlog.get_logger()
settings = get_settings()


class LockoutService:
    """Cuenta intentos fallidos de login y bloquea la cuenta.

    - ``record_failed_attempt`` persiste el intento fallido (commit inmediato
      para que el lockout sobreviva al rollback de la request).
    - ``is_locked`` devuelve ``True`` si hay >= ``LOGIN_MAX_ATTEMPTS``
      intentos fallidos dentro de ``LOGIN_LOCKOUT_MINUTES``.
    - ``reset`` elimina los intentos fallidos tras un login exitoso.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_failed_attempt(self, user_id: uuid.UUID, ip_address: str) -> None:
        """Registra un intento fallido y lo confirma en base de datos."""
        attempt = LoginAttemptModel(user_id=user_id, ip_address=ip_address, success=False)
        self._session.add(attempt)
        await self._session.commit()
        logger.warning("login_attempt_failed", user_id=str(user_id))

    async def record_successful_attempt(self, user_id: uuid.UUID, ip_address: str) -> None:
        """Registra un intento exitoso de login."""
        attempt = LoginAttemptModel(user_id=user_id, ip_address=ip_address, success=True)
        self._session.add(attempt)
        await self._session.flush()

    async def is_locked(self, user_id: uuid.UUID) -> bool:
        """Comprueba si la cuenta está temporalmente bloqueada."""
        since = datetime.now(UTC) - timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
        stmt = (
            select(func.count())
            .select_from(LoginAttemptModel)
            .where(
                LoginAttemptModel.user_id == user_id,
                LoginAttemptModel.attempted_at >= since,
                LoginAttemptModel.success.is_(False),
            )
        )
        result = await self._session.execute(stmt)
        count = result.scalar_one() or 0
        return count >= settings.LOGIN_MAX_ATTEMPTS

    async def reset(self, user_id: uuid.UUID) -> None:
        """Elimina los intentos fallidos tras un login exitoso."""
        stmt = select(LoginAttemptModel).where(
            LoginAttemptModel.user_id == user_id,
            LoginAttemptModel.success.is_(False),
        )
        result = await self._session.execute(stmt)
        attempts = list(result.scalars().all())
        for attempt in attempts:
            await self._session.delete(attempt)
        if attempts:
            await self._session.flush()
            logger.info("login_attempts_reset", user_id=str(user_id))
