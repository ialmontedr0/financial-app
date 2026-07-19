"""Wallet model - logical aggregation of financial accounts."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.user import UserModel
    from app.infrastructure.models.wallet_account import WalletAccountModel


class WalletModel(Base):
    """Wallet - logical grouping of accounts for consolidated view."""

    __tablename__ = "wallet"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    wallet_type: Mapped[str] = mapped_column(
        Enum(
            "personal",
            "business",
            "savings",
            "investment",
            "daily",
            "emergency",
            name="wallet_type",
            create_type=False,
        ),
        nullable=False,
        default="personal",
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "active",
            "archived",
            name="wallet_status",
            create_type=False,
        ),
        nullable=False,
        server_default="active",
    )

    icon: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True, default=None)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    user: Mapped[UserModel] = relationship(
        "UserModel", back_populates="wallets", lazy="noload"
    )
    wallet_accounts: Mapped[list[WalletAccountModel]] = relationship(
        "WalletAccountModel",
        back_populates="wallet",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<WalletModel(id={self.id}, name={self.name}, type={self.wallet_type})>"
