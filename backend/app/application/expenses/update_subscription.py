"""Use case: Update a subscription."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class UpdateSubscriptionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(
        self, user_id: uuid.UUID, subscription_id: uuid.UUID, *, changes: dict[str, Any]
    ) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        allowed_fields = {
            "name",
            "amount",
            "billing_frequency",
            "category_id",
            "status",
            "start_date",
            "end_date",
            "website_url",
            "notes",
        }
        filtered = {k: v for k, v in changes.items() if k in allowed_fields}

        if "billing_frequency" in filtered:
            valid_frequencies = {"monthly", "quarterly", "bimonthly", "yearly"}
            if filtered["billing_frequency"] not in valid_frequencies:
                raise ValidationError(
                    f"billing_frequency no valido: {filtered['billing_frequency']}"
                )

        if "status" in filtered:
            valid_statuses = {"active", "paused", "cancelled", "trial", "expired"}
            if filtered["status"] not in valid_statuses:
                raise ValidationError(f"status no valido: {filtered['status']}")

        if "amount" in filtered:
            try:
                filtered["amount"] = float(filtered["amount"])
            except (TypeError, ValueError):
                pass
            if filtered["amount"] <= 0:
                raise ValidationError("amount debe ser mayor a 0")

        if not filtered:
            return {"message": "No changes detected"}

        updated = await self._repo.update_subscription(subscription_id, user_id, **filtered)
        if updated is None:
            raise NotFoundError("Subscription")

        return {
            "id": str(updated.id),
            "name": updated.name,
            "amount": str(updated.amount),
            "billing_frequency": updated.billing_frequency,
            "status": updated.status,
            "category_id": str(updated.category_id) if updated.category_id else None,
            "start_date": updated.start_date.isoformat() if updated.start_date else None,
            "end_date": updated.end_date.isoformat() if updated.end_date else None,
            "website_url": updated.website_url,
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
        }
