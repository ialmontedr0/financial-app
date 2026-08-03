from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base

if TYPE_CHECKING:  # pragma: no cover
    from app.infrastructure.models.insurance_policy import InsurancePolicyModel
    from app.infrastructure.models.insurance_premium import InsurancePremiumModel
    from app.infrastructure.models.user import UserModel


class InsuranceModel(Base):
    __tablename__ = "insurance"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum(
            "life",
            "health",
            "auto",
            "home",
            "travel",
            "disability",
            "other",
            name="insurance_type_enum",
            create_type=False,
        ),
        nullable=False,
        default="other",
    )
    provider: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    policy_number: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    status: Mapped[str] = mapped_column(
        Enum(
            "active",
            "cancelled",
            "expired",
            "pending",
            name="insurance_status_enum",
            create_type=False,
        ),
        nullable=False,
        default="active",
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    coverage_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=19, scale=4), nullable=True, default=None
    )
    premium_amount: Mapped[Decimal] = mapped_column(Numeric(precision=19, scale=4), nullable=False)
    premium_frequency: Mapped[str] = mapped_column(
        Enum(
            "monthly",
            "quarterly",
            "semi_annual",
            "annual",
            name="premium_frequency_enum",
            create_type=False,
        ),
        nullable=False,
        default="monthly",
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # relationships
    user: Mapped[UserModel] = relationship("UserModel", lazy="noload")
    policies: Mapped[list[InsurancePolicyModel]] = relationship(
        back_populates="insurance", lazy="selectin", cascade="all, delete-orphan"
    )
    premiums: Mapped[list[InsurancePremiumModel]] = relationship(
        back_populates="insurance", lazy="selectin", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_insurance_user_status", "user_id", "status"),)

    def __repr__(self) -> str:
        return f"<Insurance {self.name} | {self.type} | {self.status}>"
