"""Use case: Update a credit card."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class UpdateCardUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(
        self, user_id: uuid.UUID, card_id: uuid.UUID, *, changes: dict[str, Any]
    ) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        allowed_fields = {
            "name",
            "last_four_digits",
            "card_network",
            "currency_code",
            "is_multicurrency",
            "secondary_currency_code",
            "secondary_credit_limit",
            "secondary_available_credit",
            "credit_limit",
            "available_credit",
            "statement_day",
            "payment_due_day",
            "interest_rate",
            "is_active",
            "include_in_totals",
            "color",
            "icon",
        }
        filtered = {k: v for k, v in changes.items() if k in allowed_fields}

        if "statement_day" in filtered:
            day = filtered["statement_day"]
            if day is not None and not (1 <= day <= 28):
                raise ValidationError("statement_day debe ser entre 1 y 28")

        if "payment_due_day" in filtered:
            day = filtered["payment_due_day"]
            if day is not None and not (1 <= day <= 28):
                raise ValidationError("payment_due_day debe ser entre 1 y 28")

        if "credit_limit" in filtered:
            try:
                filtered["credit_limit"] = float(filtered["credit_limit"])
            except (TypeError, ValueError):
                pass
            if filtered["credit_limit"] is not None and filtered["credit_limit"] <= 0:
                raise ValidationError("credit_limit debe ser mayor a 0")

        if not filtered:
            return {"message": "No changes detected"}

        updated = await self._repo.update_card(card_id, user_id, **filtered)
        if updated is None:
            raise NotFoundError("CreditCard")

        return {
            "id": str(updated.id),
            "name": updated.name,
            "account_id": str(updated.account_id) if updated.account_id else None,
            "last_four_digits": updated.last_four_digits,
            "card_network": updated.card_network,
            "currency_code": updated.currency_code,
            "is_multicurrency": updated.is_multicurrency,
            "secondary_currency_code": updated.secondary_currency_code,
            "secondary_credit_limit": str(updated.secondary_credit_limit)
            if updated.secondary_credit_limit
            else None,
            "secondary_available_credit": str(updated.secondary_available_credit)
            if updated.secondary_available_credit
            else None,
            "credit_limit": str(updated.credit_limit) if updated.credit_limit else None,
            "available_credit": str(updated.available_credit)
            if updated.available_credit is not None
            else None,
            "statement_day": updated.statement_day,
            "payment_due_day": updated.payment_due_day,
            "interest_rate": str(updated.interest_rate) if updated.interest_rate else None,
            "is_active": updated.is_active,
            "include_in_totals": updated.include_in_totals,
            "color": updated.color,
            "icon": updated.icon,
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
        }
