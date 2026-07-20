"""Use case: Create an expense service (utility provider)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateServiceUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        name: str,
        service_type: str | None = None,
        provider_name: str | None = None,
        account_number: str | None = None,
        category_id: uuid.UUID | None = None,
        due_day: int | None = None,
        estimated_amount: float | None = None,
        notes: str | None = None,
    ) -> dict:
        from app.middleware.error_handler import ValidationError

        if not name or not name.strip():
            raise ValidationError("Service name es requerido")

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
        if service_type and service_type not in valid_types:
            raise ValidationError(
                f"service_type no valido: {service_type}. Soportado: {', '.join(sorted(valid_types))}"
            )

        if due_day is not None and (due_day < 1 or due_day > 31):
            raise ValidationError("due_day debe ser entre 1 y 31")

        if estimated_amount is not None and estimated_amount < 0:
            raise ValidationError("estimated_amount no puede ser negativo")

        service = await self._repo.create_service(
            user_id,
            name=name.strip(),
            service_type=service_type,
            provider=provider_name,
            account_number=account_number,
            category_id=category_id,
            due_day=due_day,
            estimated_amount=estimated_amount,
            notes=notes,
        )

        return {
            "id": str(service.id),
            "name": service.name,
            "service_type": service.service_type,
            "provider_name": service.provider,
            "account_number": service.account_number,
            "category_id": str(service.category_id) if service.category_id else None,
            "due_day": service.due_day,
            "estimated_amount": str(service.estimated_amount) if service.estimated_amount else None,
            "is_active": service.is_active,
            "notes": service.notes,
            "created_at": service.created_at.isoformat() if service.created_at else None,
        }
