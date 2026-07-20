"""Use case: Update an expense service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class UpdateServiceUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(
        self, user_id: uuid.UUID, service_id: uuid.UUID, *, changes: dict[str, Any]
    ) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        allowed_fields = {
            "name",
            "service_type",
            "provider",
            "account_number",
            "category_id",
            "due_day",
            "estimated_amount",
            "is_active",
            "notes",
        }
        filtered = {k: v for k, v in changes.items() if k in allowed_fields}

        if "service_type" in filtered:
            valid_types = {
                "electric",
                "water",
                "gas",
                "internet",
                "phone",
                "insurance",
                "rent",
                "mortgage",
                "other",
            }
            if filtered["service_type"] not in valid_types:
                raise ValidationError(f"service_type no valido: {filtered['service_type']}")

        if "due_day" in filtered:  # noqa: SIM102
            if filtered["due_day"] is not None and (
                filtered["due_day"] < 1 or filtered["due_day"] > 31
            ):
                raise ValidationError("due_day debe ser entre 1 y 31")

        if not filtered:
            return {"message": "No changes detected"}

        updated = await self._repo.update_service(service_id, user_id, **filtered)
        if updated is None:
            raise NotFoundError("Service")

        return {
            "id": str(updated.id),
            "name": updated.name,
            "service_type": updated.service_type,
            "provider_name": updated.provider,
            "account_number": updated.account_number,
            "category_id": str(updated.category_id) if updated.category_id else None,
            "due_day": updated.due_day,
            "estimated_amount": str(updated.estimated_amount) if updated.estimated_amount else None,
            "is_active": updated.is_active,
            "notes": updated.notes,
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
        }
