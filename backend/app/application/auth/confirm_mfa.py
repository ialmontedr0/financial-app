import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.events import MFAEnabledEvent
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.mfa_service import MFAService

logger = structlog.get_logger()


class ConfirmMFAUseCase:
    """Enable MFA after verifying a valid TOTP code against the pending secret."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)

    async def execute(self, user_id: uuid.UUID, code: str) -> dict:
        """Verify the TOTP code and enable MFA."""
        from app.middleware.error_handler import NotFoundError, UnauthorizedError, ValidationError

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User")

        if user.mfa_enabled:
            raise ValidationError("MFA is already enabled for this account")

        if not user.mfa_secret:
            raise ValidationError("MFA setup not initiated. Call /auth/mfa/enable first")

        if not MFAService.verify_code(user.mfa_secret, code):
            raise UnauthorizedError("Invalid MFA code")

        # Code valid — enable MFA permanently
        await self._user_repo.update_mfa_secret(user_id, user.mfa_secret)

        event = MFAEnabledEvent(user_id=user_id)
        logger.info("mfa_enabled", event_type=event.event_type, user_id=str(user_id))

        return {"message": "MFA enabled successfully"}
