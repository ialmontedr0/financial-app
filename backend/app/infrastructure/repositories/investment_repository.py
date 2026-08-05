"""Investment repository — all database operations for assets, portfolios and transactions."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.investment import (
    AssetModel,
    AssetPriceHistoryModel,
    InvestmentTransactionModel,
    PortfolioAssetModel,
    PortfolioModel,
)

logger = structlog.get_logger()


class InvestmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── ASSETS ──────────────────────────────────────────────────

    async def create_asset(self, user_id: uuid.UUID, **kwargs: object) -> AssetModel:
        asset = AssetModel(user_id=user_id, **kwargs)
        self._session.add(asset)
        await self._session.flush()
        logger.info("investment_asset_created", asset_id=str(asset.id), user_id=str(user_id))
        return asset

    async def get_asset(self, asset_id: uuid.UUID, user_id: uuid.UUID) -> AssetModel | None:
        stmt = select(AssetModel).where(
            AssetModel.id == asset_id,
            AssetModel.user_id == user_id,
            AssetModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_assets(self, user_id: uuid.UUID) -> list[AssetModel]:
        stmt = (
            select(AssetModel)
            .where(AssetModel.user_id == user_id, AssetModel.deleted_at.is_(None))
            .order_by(AssetModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_asset(self, asset: AssetModel, **kwargs: object) -> AssetModel:
        for key, value in kwargs.items():
            setattr(asset, key, value)
        await self._session.flush()
        await self._session.refresh(asset)
        return asset

    async def delete_asset(self, asset: AssetModel) -> bool:
        asset.deleted_at = datetime.now(UTC)
        await self._session.flush()
        logger.info("investment_asset_deleted", asset_id=str(asset.id))
        return True

    # ── PORTFOLIOS ──────────────────────────────────────────────

    async def create_portfolio(self, user_id: uuid.UUID, **kwargs: object) -> PortfolioModel:
        portfolio = PortfolioModel(user_id=user_id, **kwargs)
        self._session.add(portfolio)
        await self._session.flush()
        logger.info(
            "investment_portfolio_created", portfolio_id=str(portfolio.id), user_id=str(user_id)
        )
        return portfolio

    async def get_portfolio(
        self, portfolio_id: uuid.UUID, user_id: uuid.UUID
    ) -> PortfolioModel | None:
        stmt = select(PortfolioModel).where(
            PortfolioModel.id == portfolio_id,
            PortfolioModel.user_id == user_id,
            PortfolioModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_portfolios(self, user_id: uuid.UUID) -> list[PortfolioModel]:
        stmt = (
            select(PortfolioModel)
            .where(PortfolioModel.user_id == user_id, PortfolioModel.deleted_at.is_(None))
            .order_by(PortfolioModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_portfolio(self, portfolio: PortfolioModel) -> bool:
        portfolio.deleted_at = datetime.now(UTC)
        await self._session.flush()
        logger.info("investment_portfolio_deleted", portfolio_id=str(portfolio.id))
        return True

    # ── PORTFOLIO ASSETS ────────────────────────────────────────

    async def get_portfolio_asset(
        self, portfolio_id: uuid.UUID, asset_id: uuid.UUID
    ) -> PortfolioAssetModel | None:
        stmt = select(PortfolioAssetModel).where(
            PortfolioAssetModel.portfolio_id == portfolio_id,
            PortfolioAssetModel.asset_id == asset_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_portfolio_asset(
        self, portfolio_id: uuid.UUID, asset_id: uuid.UUID, **kwargs: object
    ) -> PortfolioAssetModel:
        pa = PortfolioAssetModel(portfolio_id=portfolio_id, asset_id=asset_id, **kwargs)
        self._session.add(pa)
        await self._session.flush()
        logger.info(
            "investment_portfolio_asset_created",
            portfolio_id=str(portfolio_id),
            asset_id=str(asset_id),
        )
        return pa

    async def update_portfolio_asset(
        self, pa: PortfolioAssetModel, **kwargs: object
    ) -> PortfolioAssetModel:
        for key, value in kwargs.items():
            setattr(pa, key, value)
        await self._session.flush()
        await self._session.refresh(pa)
        return pa

    async def list_portfolio_assets(self, portfolio_id: uuid.UUID) -> list[PortfolioAssetModel]:
        stmt = (
            select(PortfolioAssetModel)
            .where(PortfolioAssetModel.portfolio_id == portfolio_id)
            .order_by(PortfolioAssetModel.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_assets_in_portfolios(
        self, portfolio_ids: list[uuid.UUID]
    ) -> list[PortfolioAssetModel]:
        stmt = select(PortfolioAssetModel).where(
            PortfolioAssetModel.portfolio_id.in_(portfolio_ids)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── TRANSACTIONS ────────────────────────────────────────────

    async def create_transaction(self, **kwargs: object) -> InvestmentTransactionModel:
        tx = InvestmentTransactionModel(**kwargs)
        self._session.add(tx)
        await self._session.flush()
        logger.info("investment_transaction_created", tx_id=str(tx.id))
        return tx

    async def list_asset_transactions(
        self, asset_id: uuid.UUID
    ) -> list[InvestmentTransactionModel]:
        stmt = (
            select(InvestmentTransactionModel)
            .where(InvestmentTransactionModel.asset_id == asset_id)
            .order_by(InvestmentTransactionModel.date.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_portfolio_transactions(
        self, portfolio_id: uuid.UUID
    ) -> list[InvestmentTransactionModel]:
        stmt = (
            select(InvestmentTransactionModel)
            .where(InvestmentTransactionModel.portfolio_id == portfolio_id)
            .order_by(InvestmentTransactionModel.date.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_user_transactions(self, user_id: uuid.UUID) -> list[InvestmentTransactionModel]:
        stmt = (
            select(InvestmentTransactionModel)
            .join(AssetModel, AssetModel.id == InvestmentTransactionModel.asset_id)
            .where(
                AssetModel.user_id == user_id,
                AssetModel.deleted_at.is_(None),
            )
            .order_by(InvestmentTransactionModel.date.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ── PRICE HISTORY ───────────────────────────────────────────

    async def upsert_price_point(
        self,
        asset_id: uuid.UUID,
        price_date: date,
        close_price: Decimal,
        open_price: Decimal | None = None,
        high_price: Decimal | None = None,
        low_price: Decimal | None = None,
        volume: Decimal | None = None,
    ) -> AssetPriceHistoryModel:
        stmt = select(AssetPriceHistoryModel).where(
            AssetPriceHistoryModel.asset_id == asset_id,
            AssetPriceHistoryModel.date == price_date,
        )
        result = await self._session.execute(stmt)
        point = result.scalar_one_or_none()
        if point is None:
            point = AssetPriceHistoryModel(
                asset_id=asset_id,
                date=price_date,
                open_price=open_price,
                close_price=close_price,
                high_price=high_price,
                low_price=low_price,
                volume=volume,
            )
            self._session.add(point)
        else:
            point.close_price = close_price
            if open_price is not None:
                point.open_price = open_price
            if high_price is not None:
                point.high_price = high_price
            if low_price is not None:
                point.low_price = low_price
            if volume is not None:
                point.volume = volume
        await self._session.flush()
        return point

    async def list_price_history(
        self, asset_id: uuid.UUID, limit: int = 90
    ) -> list[AssetPriceHistoryModel]:
        stmt = (
            select(AssetPriceHistoryModel)
            .where(AssetPriceHistoryModel.asset_id == asset_id)
            .order_by(AssetPriceHistoryModel.date.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        points = list(result.scalars().all())
        points.reverse()
        return points

    # ── HELPERS ─────────────────────────────────────────────────

    async def get_assets_by_ids(self, asset_ids: list[uuid.UUID]) -> dict[uuid.UUID, AssetModel]:
        stmt = select(AssetModel).where(AssetModel.id.in_(asset_ids))
        result = await self._session.execute(stmt)
        return {asset.id: asset for asset in result.scalars().all()}

    async def count_assets(self, user_id: uuid.UUID) -> int:
        stmt = select(AssetModel).where(
            AssetModel.user_id == user_id, AssetModel.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        return len(list(result.scalars().all()))
