"""Use case: Soft-delete user account."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.user_repository import UserRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteUserAccountUseCase:
    """Soft-delete the authenticated user's account.

    Revokes all sessions and marks the user as deleted.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        """Soft-delete user account."""
        from app.middleware.error_handler import NotFoundError

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User")

        # Soft-delete
        await self._user_repo.soft_delete(user_id)

        # Revoke all sessions
        from app.infrastructure.cache.session_store import SessionStore

        session_store = SessionStore()
        revoked_count = await session_store.revoke_all_user_sessions(str(user_id))

        logger.info(
            "user_account_deleted",
            user_id=str(user_id),
            sessions_revoked=revoked_count,
        )

        return {
            "message": "Account deleted successfully",
            "sessions_revoked": revoked_count,
        }
