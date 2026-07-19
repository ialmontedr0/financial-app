import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.events import MFADisabledEvent
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.mfa_service import MFAService

logger = structlog.get_logger()


class DisableMFAUseCase:
    """Disable MFA for a user after verifying current TOTP code."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)

    async def execute(self, user_id: uuid.UUID, code: str) -> dict:
        """Verify code and disable MFA."""
        from app.middleware.error_handler import UnauthorizedError, ValidationError

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            from app.middleware.error_handler import NotFoundError

            raise NotFoundError("User")

        if not user.mfa_enabled:
            raise ValidationError("MFA is not enabled")

        if not user.mfa_secret:
            raise ValidationError("MFA secret not configured")

        # Verify the code before disabling
        if not MFAService.verify_code(user.mfa_secret, code):
            raise UnauthorizedError("Invalid MFA code")

        # Disable MFA
        await self._user_repo.disable_mfa(user_id)

        event = MFADisabledEvent(user_id=user_id)
        logger.info("mfa_disabled", event_type=event.event_type, user_id=str(user_id))

        return {"message": "MFA disabled successfully"}
