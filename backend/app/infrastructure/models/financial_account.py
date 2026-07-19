"""Financial Account model — bank, cash, savings, checking, wallet, crypto."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:
    from app.infrastructure.models.user import UserModel


class FinancialAccountModel(Base):
    """Financial account — one per bank/cash/wallet/crypto instance."""

    __tablename__ = "financial_account"

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

    # --- Identity ---
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[str] = mapped_column(
        Enum(
            "bank",
            "cash",
            "savings",
            "checking",
            "wallet",
            "crypto",
            name="account_type",
            create_type=False,
        ),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "active",
            "inactive",
            "archived",
            "frozen",
            name="account_status",
            create_type=False,
        ),
        nullable=False,
        server_default="active",
    )

    # --- Financial ---
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="DOP")
    balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4),
        nullable=False,
        server_default="0",
    )
    initial_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=19, scale=4),
        nullable=False,
        server_default="0",
    )

    # --- Institution Info ---
    institution: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    account_number_last4: Mapped[str | None] = mapped_column(
        String(4), nullable=True, default=None
    )

    # --- Display ---
    icon: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True, default=None)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    # --- Settings ---
    include_in_net_worth: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    include_in_totals: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- Timestamps ---
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

    # --- Relationship ---
    user: Mapped[UserModel] = relationship("UserModel", back_populates="accounts", lazy="noload")

    def __repr__(self) -> str:
        return (
            f"<FinancialAccountModel(id={self.id}, name={self.name}, "
            f"type={self.account_type}, balance={self.balance} {self.currency_code})>"
        )
