"""Use case: Create a subscription (recurring expense)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateSubscriptionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        name: str,
        amount: float,
        billing_frequency: str = "monthly",
        category_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        website_url: str | None = None,
        notes: str | None = None,
    ) -> dict:
        from app.middleware.error_handler import ValidationError

        if not name or not name.strip():
            raise ValidationError("Subscription name es requerido")
        if amount <= 0:
            raise ValidationError("amount debe ser mayor a 0")

        valid_frequencies = {"monthly", "quarterly", "bimonthly", "yearly"}
        if billing_frequency not in valid_frequencies:
            raise ValidationError(
                f"billing_frequency no valido: {billing_frequency}. Soportado: {', '.join(sorted(valid_frequencies))}"
            )

        if end_date and start_date and end_date < start_date:
            raise ValidationError("end_date no puede ser anterior a start_date")

        sub = await self._repo.create_subscription(
            user_id,
            name=name.strip(),
            amount=amount,
            billing_frequency=billing_frequency,
            category_id=category_id,
            start_date=start_date,
            end_date=end_date,
            website_url=website_url,
        )

        return {
            "id": str(sub.id),
            "name": sub.name,
            "amount": str(sub.amount),
            "billing_frequency": sub.billing_frequency,
            "status": sub.status,
            "category_id": str(sub.category_id) if sub.category_id else None,
            "start_date": sub.start_date.isoformat() if sub.start_date else None,
            "end_date": sub.end_date.isoformat() if sub.end_date else None,
            "website_url": sub.website_url,
            "created_at": sub.created_at.isoformat() if sub.created_at else None,
        }
