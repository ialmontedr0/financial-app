"""Use case: Update an income source."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class UpdateSourceUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncomeRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        source_id: uuid.UUID,
        *,
        changes: dict[str, Any],
    ) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        source = await self._repo.get_source_by_id(source_id, user_id)
        if source is None:
            raise NotFoundError("IncomeSource")

        allowed_fields = {"name", "income_type", "stability", "frequency", "expected_amount", "default_account_id", "default_category_id", "default_currency", "notes", "is_active"}

        if "income_type" in changes:
            valid_types = {"salary", "freelance", "business", "investment", "rental", "refund", "gift", "bonus", "commission", "other"}
            if changes["income_type"] not in valid_types:
                raise ValidationError(f"income_type no valido: {changes['income_type']}")

        if "stability" in changes:
            valid_stability = {"fixed", "variable", "irregular", "one_time"}
            if changes["stability"] not in valid_stability:
                raise ValidationError(f"stability no valido: {changes['stability']}")

        filtered = {k: v for k, v in changes.items() if k in allowed_fields}
        if not filtered:
            return {"message": "No changes detected"}

        updated = await self._repo.update_source(source_id, user_id, **filtered)
        if updated is None:
            raise NotFoundError("IncomeSource")

        return {
            "id": str(updated.id),
            "name": updated.name,
            "income_type": updated.income_type,
            "stability": updated.stability,
            "frequency": updated.frequency,
            "expected_amount": str(updated.default_amount) if updated.default_amount else None,
            "default_account_id": str(updated.default_account_id) if updated.default_account_id else None,
            "default_category_id": str(updated.default_category_id) if updated.default_category_id else None,
            "default_currency": updated.default_currency,
            "is_active": updated.is_active,
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
        }
