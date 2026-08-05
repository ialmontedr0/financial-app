"""Investment domain ORM models: assets, transactions, price history, portfolios."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from app.infrastructure.models.user import UserModel


class AssetModel(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None, index=True)
    asset_type: Mapped[str] = mapped_column(
        Enum(
            "stock",
            "bond",
            "etf",
            "crypto",
            "mutual_fund",
            "real_estate",
            "commodity",
            name="asset_type_enum",
            create_type=False,
        ),
        nullable=False,
        default="stock",
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    current_price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # relationships
    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")

    __table_args__ = (Index("ix_asset_user_type", "user_id", "asset_type"),)

    def __repr__(self) -> str:
        return f"<Asset {self.name} | {self.asset_type}>"


class PortfolioModel(Base):
    __tablename__ = "portfolios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # relationships
    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")

    def __repr__(self) -> str:
        return f"<Portfolio {self.name}>"


class PortfolioAssetModel(Base):
    __tablename__ = "portfolio_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=8), nullable=False, default=Decimal("0")
    )
    cost_basis: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=Decimal("0")
    )
    average_price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("portfolio_id", "asset_id", name="uq_portfolio_assets_portfolio_asset"),
    )

    def __repr__(self) -> str:
        return f"<PortfolioAsset portfolio={self.portfolio_id} asset={self.asset_id} qty={self.quantity}>"


class InvestmentTransactionModel(Base):
    __tablename__ = "investment_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    portfolio_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=True,
        default=None,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        Enum(
            "buy",
            "sell",
            "dividend",
            "fee",
            name="investment_tx_type_enum",
            create_type=False,
        ),
        nullable=False,
        default="buy",
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=8), nullable=False)
    price_per_unit: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    fees: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4), nullable=False, default=Decimal("0")
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # relationships
    asset: Mapped[AssetModel] = relationship("AssetModel", lazy="noload")
    portfolio: Mapped[PortfolioModel | None] = relationship("PortfolioModel", lazy="noload")

    __table_args__ = (Index("ix_investment_tx_asset_date", "asset_id", "date"),)

    def __repr__(self) -> str:
        return f"<InvestmentTransaction {self.type} qty={self.quantity}>"


class AssetPriceHistoryModel(Base):
    __tablename__ = "asset_price_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    open_price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    close_price: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    high_price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    low_price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    volume: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=2), nullable=True, default=None
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("asset_id", "date", name="uq_asset_price_history_asset_date"),
        Index("ix_asset_price_history_asset_date", "asset_id", "date"),
    )

    def __repr__(self) -> str:
        return f"<AssetPriceHistory asset={self.asset_id} date={self.date}>"
