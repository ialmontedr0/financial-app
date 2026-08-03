"""Currency exchange rate model — daily historical rates between ISO 4217 pairs."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class CurrencyExchangeRateModel(Base):
    """A single exchange rate for a currency pair on a given day.

    Rates are global (not per-user): they represent the market price of one
    unit of ``source_currency`` expressed in ``target_currency``.
    """

    __tablename__ = "currency_exchange_rate"
    __table_args__ = (
        UniqueConstraint(
            "source_currency",
            "target_currency",
            "rate_date",
            name="uq_currency_exchange_rate_pair_date",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=8), nullable=False)
    rate_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<CurrencyExchangeRateModel(id={self.id}, "
            f"{self.source_currency}->{self.target_currency} "
            f"= {self.rate} @ {self.rate_date})>"
        )
