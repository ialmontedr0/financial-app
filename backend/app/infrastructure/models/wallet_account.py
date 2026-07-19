"""Wallet-Account junction model - many-to-many relationship."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.financial_account import FinancialAccountModel
    from app.infrastructure.models.wallet import WalletModel


class WalletAccountModel(Base):
    """Junction table linking wallets to financial accounts."""

    __tablename__ = "wallet_account"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wallet.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    wallet: Mapped[WalletModel] = relationship(
        "WalletModel", back_populates="wallet_accounts", lazy="noload"
    )
    account: Mapped[FinancialAccountModel] = relationship(
        "FinancialAccountModel", lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<WalletAccountModel(wallet_id={self.wallet_id}, "
            f"account_id={self.account_id})>"
        )
