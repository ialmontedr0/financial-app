"""Use case: Soft-delete a financial account."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.account_repository import AccountRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteAccountUseCase:
    """Soft-delete a financial account."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AccountRepository(session)

    async def execute(self, user_id: uuid.UUID, account_id: uuid.UUID) -> dict:
        """Soft-delete the account."""
        from app.middleware.error_handler import NotFoundError

        account = await self._repo.get_by_id(account_id, user_id)
        if account is None:
            raise NotFoundError("Account")

        await self._repo.soft_delete(account_id, user_id)

        logger.info(
            "account_deleted",
            user_id=str(user_id),
            account_id=str(account_id),
            name=account.name,
        )

        return {
            "message": f"Cuenta '{account.name}' eliminada exitosamente",
            "account_id": str(account_id),
        }
