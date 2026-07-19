import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.events import MFAEnabledEvent
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.mfa_service import MFAService

logger = structlog.get_logger()


class EnableMFAUseCase:
    """Enable MFA for a user. Returns QR code and secret."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        """Enable MFA and return setup data."""
        from app.middleware.error_handler import ValidationError

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            from app.middleware.error_handler import NotFoundError

            raise NotFoundError("User")

        if user.mfa_enabled:
            raise ValidationError("MFA is already enabled for this account")

        # Generate MFA setup
        secret, uri, qr_b64 = MFAService.generate_mfa_setup(user.email)

        # Store secret (not yet enabled — will be enabled after verification)
        await self._user_repo.update_mfa_secret(user_id, secret)

        event = MFAEnabledEvent(user_id=user_id)
        logger.info("mfa_setup_initiated", event_type=event.event_type, user_id=str(user_id))

        return {
            "secret": secret,
            "qr_code_base64": qr_b64,
            "message": "Scan the QR code with your authenticator app, then verify with a code",
        }
