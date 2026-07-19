"""Repository for wallet persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func, select

from app.infrastructure.models.financial_account import FinancialAccountModel
from app.infrastructure.models.wallet import WalletModel
from app.infrastructure.models.wallet_account import WalletAccountModel

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class WalletRepository:
    """Repository for WalletModel operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        **kwargs: str | int | bool | None,
    ) -> WalletModel:
        """Create a new wallet."""
        wallet = WalletModel(user_id=user_id, **kwargs)
        self._session.add(wallet)
        await self._session.flush()
        logger.info(
            "wallet_created",
            user_id=str(user_id),
            wallet_id=str(wallet.id),
            name=wallet.name,
            wallet_type=wallet.wallet_type,
        )
        return wallet

    async def get_by_id(
        self,
        wallet_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WalletModel | None:
        """Get wallet by ID, scoped to user. Excludes soft-deleted."""
        stmt = (
            select(WalletModel)
            .where(
                WalletModel.id == wallet_id,
                WalletModel.user_id == user_id,
                WalletModel.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        wallet_type: str | None = None,
    ) -> list[WalletModel]:
        """List all wallets for a user, optionally filtered by type."""
        stmt = select(WalletModel).where(
            WalletModel.user_id == user_id,
            WalletModel.deleted_at.is_(None),
        )
        if wallet_type:
            stmt = stmt.where(WalletModel.wallet_type == wallet_type)
        stmt = stmt.order_by(
            WalletModel.sort_order.asc(),
            WalletModel.name.asc(),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        wallet_id: uuid.UUID,
        user_id: uuid.UUID,
        **kwargs: str | int | bool | None,
    ) -> WalletModel | None:
        """Update wallet fields. Returns None if not found."""
        wallet = await self.get_by_id(wallet_id, user_id)
        if wallet is None:
            return None
        for key, value in kwargs.items():
            if hasattr(wallet, key):
                setattr(wallet, key, value)
        await self._session.flush()
        await self._session.refresh(wallet)
        logger.info(
            "wallet_updated",
            user_id=str(user_id),
            wallet_id=str(wallet_id),
            fields=list(kwargs.keys()),
        )
        return wallet

    async def soft_delete(
        self,
        wallet_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WalletModel | None:
        """Soft-delete a wallet by setting deleted_at."""
        from datetime import UTC, datetime

        return await self.update(
            wallet_id,
            user_id,
            deleted_at=datetime.now(UTC),
            status="archived",
        )

    async def add_account(
        self,
        wallet_id: uuid.UUID,
        account_id: uuid.UUID,
        user_id: uuid.UUID,
        notes: str | None = None,
    ) -> WalletAccountModel | None:
        """Add an account to a wallet. Returns None if account not found or not owned by user."""
        account_stmt = select(FinancialAccountModel).where(
            FinancialAccountModel.id == account_id,
            FinancialAccountModel.user_id == user_id,
            FinancialAccountModel.deleted_at.is_(None),
        )
        account_result = await self._session.execute(account_stmt)
        account = account_result.scalar_one_or_none()
        if account is None:
            return None

        existing_stmt = select(WalletAccountModel).where(
            WalletAccountModel.wallet_id == wallet_id,
            WalletAccountModel.account_id == account_id,
        )
        existing = (await self._session.execute(existing_stmt)).scalar_one_or_none()
        if existing is not None:
            return existing

        wa = WalletAccountModel(
            wallet_id=wallet_id,
            account_id=account_id,
            notes=notes,
        )
        self._session.add(wa)
        await self._session.flush()
        logger.info(
            "wallet_account_added",
            wallet_id=str(wallet_id),
            account_id=str(account_id),
        )
        return wa

    async def remove_account(
        self,
        wallet_id: uuid.UUID,
        account_id: uuid.UUID,
    ) -> bool:
        """Remove an account from a wallet. Returns True if removed."""
        stmt = select(WalletAccountModel).where(
            WalletAccountModel.wallet_id == wallet_id,
            WalletAccountModel.account_id == account_id,
        )
        result = await self._session.execute(stmt)
        wa = result.scalar_one_or_none()
        if wa is None:
            return False
        await self._session.delete(wa)
        await self._session.flush()
        logger.info(
            "wallet_account_removed",
            wallet_id=str(wallet_id),
            account_id=str(account_id),
        )
        return True

    async def get_wallet_account_ids(
        self,
        wallet_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        """Get all account IDs linked to a wallet."""
        stmt = (
            select(WalletAccountModel.account_id)
            .where(WalletAccountModel.wallet_id == wallet_id)
        )
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_wallet_balance(
        self,
        wallet_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict:
        """Compute wallet balance from linked active accounts."""
        account_ids = await self.get_wallet_account_ids(wallet_id)
        if not account_ids:
            return {"total_accounts": 0, "by_currency": {}}

        stmt = (
            select(
                FinancialAccountModel.currency_code,
                func.count(FinancialAccountModel.id).label("account_count"),
                func.sum(FinancialAccountModel.balance).label("total_balance"),
            )
            .where(
                FinancialAccountModel.id.in_(account_ids),
                FinancialAccountModel.user_id == user_id,
                FinancialAccountModel.deleted_at.is_(None),
                FinancialAccountModel.status == "active",
                FinancialAccountModel.include_in_totals.is_(True),
            )
            .group_by(FinancialAccountModel.currency_code)
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        count_stmt = (
            select(func.count(FinancialAccountModel.id))
            .where(
                FinancialAccountModel.id.in_(account_ids),
                FinancialAccountModel.user_id == user_id,
                FinancialAccountModel.deleted_at.is_(None),
                FinancialAccountModel.status == "active",
            )
        )
        total_count = (await self._session.execute(count_stmt)).scalar() or 0

        breakdown: dict[str, dict] = {}
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

    async def get_wallet_liquidity(
        self,
        wallet_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict:
        """Compute liquidity breakdown for a wallet based on account types."""
        account_ids = await self.get_wallet_account_ids(wallet_id)
        if not account_ids:
            return {
                "overall_level": "high",
                "breakdown": {},
                "total_accounts": 0,
            }

        stmt = select(
            FinancialAccountModel.account_type,
            func.count(FinancialAccountModel.id).label("count"),
            func.sum(FinancialAccountModel.balance).label("total"),
        ).where(
            FinancialAccountModel.id.in_(account_ids),
            FinancialAccountModel.user_id == user_id,
            FinancialAccountModel.deleted_at.is_(None),
            FinancialAccountModel.status == "active",
        ).group_by(FinancialAccountModel.account_type)

        result = await self._session.execute(stmt)
        rows = result.all()

        HIGH_LIQUIDITY = {"cash", "checking", "wallet"}
        MEDIUM_LIQUIDITY = {"savings"}

        level_scores: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
        breakdown: dict[str, dict] = {}
        total_count = 0

        for row in rows:
            total_count += row.count
            at = row.account_type
            if at in HIGH_LIQUIDITY:
                level = "high"
            elif at in MEDIUM_LIQUIDITY:
                level = "medium"
            else:
                level = "low"
            level_scores[level] += 1
            breakdown[at] = {
                "account_type": at,
                "account_count": row.count,
                "total_balance": str(row.total or 0),
                "liquidity_level": level,
            }

        if level_scores["low"] > 0:
            overall = "low"
        elif level_scores["medium"] > 0 and level_scores["high"] == 0:
            overall = "medium"
        elif level_scores["medium"] > 0 and level_scores["high"] > 0:
            overall = "mixed"
        else:
            overall = "high"

        return {
            "overall_level": overall,
            "breakdown": breakdown,
            "total_accounts": total_count,
        }
