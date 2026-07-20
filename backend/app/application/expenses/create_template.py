"""Use case: Create an expense template (reusable defaults)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateTemplateUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        name: str,
        default_amount: float,
        default_category_id: uuid.UUID | None = None,
        default_subcategory_id: uuid.UUID | None = None,
        default_account_id: uuid.UUID | None = None,
        default_notes: str | None = None,
        default_tags: list[str] | None = None,
        default_priority: str = "normal",
        default_source: str = "manual",
        sort_order: int = 0,
    ) -> dict:
        from app.middleware.error_handler import ValidationError

        if not name or not name.strip():
            raise ValidationError("Template name es requerido")
        if default_amount <= 0:
            raise ValidationError("default_amount debe ser mayor a 0")

        valid_priorities = {"low", "normal", "high", "critical"}
        if default_priority not in valid_priorities:
            raise ValidationError(f"priority no valido: {default_priority}")

        template = await self._repo.create_template(
            user_id,
            name=name.strip(),
            description=default_notes or name.strip(),
            default_amount=default_amount,
            default_category_id=default_category_id,
            default_subcategory_id=default_subcategory_id,
            default_account_id=default_account_id,
            default_notes=default_notes,
            default_source=default_source,
            sort_order=sort_order,
        )

        return {
            "id": str(template.id),
            "name": template.name,
            "default_amount": str(template.default_amount) if template.default_amount else None,
            "default_category_id": str(template.default_category_id)
            if template.default_category_id
            else None,
            "default_subcategory_id": str(template.default_subcategory_id)
            if template.default_subcategory_id
            else None,
            "default_account_id": str(template.default_account_id)
            if template.default_account_id
            else None,
            "default_notes": template.default_notes,
            "default_source": template.default_source,
            "usage_count": template.usage_count,
            "sort_order": template.sort_order,
            "created_at": template.created_at.isoformat() if template.created_at else None,
        }
