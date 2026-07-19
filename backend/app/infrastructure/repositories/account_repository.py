"""Repository for financial account persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func, select

from app.infrastructure.models.financial_account import FinancialAccountModel

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class AccountRepository:
    """Repository for FinancialAccountModel operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        **kwargs: str | int | bool | None,
    ) -> FinancialAccountModel:
        """Create a new financial account."""
        account = FinancialAccountModel(user_id=user_id, **kwargs)
        self._session.add(account)
        await self._session.flush()
        logger.info(
            "account_created",
            user_id=str(user_id),
            account_id=str(account.id),
            name=account.name,
            account_type=account.account_type,
        )
        return account

    async def get_by_id(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> FinancialAccountModel | None:
        """Get account by ID, scoped to user. Excludes soft-deleted."""
        stmt = (
            select(FinancialAccountModel)
            .where(
                FinancialAccountModel.id == account_id,
                FinancialAccountModel.user_id == user_id,
                FinancialAccountModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        account_type: str | None = None,
        include_archived: bool = False,
    ) -> list[FinancialAccountModel]:
        """List all accounts for a user, optionally filtered by type."""
        stmt = select(FinancialAccountModel).where(
            FinancialAccountModel.user_id == user_id,
        )

        if not include_archived:
            stmt = stmt.where(FinancialAccountModel.deleted_at.is_(None))

        if account_type:
            stmt = stmt.where(FinancialAccountModel.account_type == account_type)

        stmt = stmt.order_by(
            FinancialAccountModel.sort_order.asc(),
            FinancialAccountModel.name.asc(),
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        **kwargs: str | int | bool | None,
    ) -> FinancialAccountModel | None:
        """Update account fields. Returns None if not found."""
        account = await self.get_by_id(account_id, user_id)
        if account is None:
            return None
        for key, value in kwargs.items():
            if hasattr(account, key):
                setattr(account, key, value)
        await self._session.flush()
        await self._session.refresh(account)
        logger.info(
            "account_updated",
            user_id=str(user_id),
            account_id=str(account_id),
            fields=list(kwargs.keys()),
        )
        return account

    async def soft_delete(
        self,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> FinancialAccountModel | None:
        """Soft-delete an account by setting deleted_at."""
        from datetime import UTC, datetime

        return await self.update(
            account_id,
            user_id,
            deleted_at=datetime.now(UTC),
            status="archived",
        )

    async def get_summary(self, user_id: uuid.UUID) -> dict:
        """Get aggregated account summary for a user."""
        stmt = (
            select(
                FinancialAccountModel.currency_code,
                func.count(FinancialAccountModel.id).label("account_count"),
                func.sum(FinancialAccountModel.balance).label("total_balance"),
            )
            .where(
                FinancialAccountModel.user_id == user_id,
                FinancialAccountModel.deleted_at.is_(None),
                FinancialAccountModel.include_in_totals.is_(True),
            )
            .group_by(FinancialAccountModel.currency_code)
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        count_stmt = (
            select(func.count(FinancialAccountModel.id))
            .where(
                FinancialAccountModel.user_id == user_id,
                FinancialAccountModel.deleted_at.is_(None),
            )
        )
        total_count = (await self._session.execute(count_stmt)).scalar() or 0

        breakdown = {}
        for row in rows:
            breakdown[row.currency_code] = {
                "currency": row.currency_code,
                "account_count": row.account_count,
                "total_balance": str(row.total_balance or 0),
            }

        return {
            "total_accounts": total_count,
            "by_currency": breakdown,
        }
