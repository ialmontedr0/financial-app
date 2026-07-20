"""Use case: Create an income source."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateSourceUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncomeRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        name: str,
        income_type: str = "other",
        stability: str = "fixed",
        frequency: str | None = None,
        expected_amount: float | None = None,
        default_account_id: uuid.UUID | None = None,
        default_category_id: uuid.UUID | None = None,
        default_currency: str = "DOP",
        notes: str | None = None,
    ) -> dict:
        from app.middleware.error_handler import ValidationError

        if not name or not name.strip():
            raise ValidationError("name es requerido")

        valid_types = {"salary", "freelance", "business", "investment", "rental", "refund", "gift", "bonus", "commission", "other"}
        if income_type not in valid_types:
            raise ValidationError(f"income_type no valido: {income_type}. Soportado: {', '.join(sorted(valid_types))}")

        valid_stability = {"fixed", "variable", "irregular", "one_time"}
        if stability not in valid_stability:
            raise ValidationError(f"stability no valido: {stability}. Soportado: {', '.join(sorted(valid_stability))}")

        source = await self._repo.create_source(
            user_id,
            name=str(name).strip(),
            income_type=income_type,
            stability=stability,
            frequency=frequency,
            default_amount=expected_amount,
            default_account_id=default_account_id,
            default_category_id=default_category_id,
            default_currency=default_currency,
            description=notes,
            is_active=True,
        )

        return {
            "id": str(source.id),
            "name": source.name,
            "income_type": source.income_type,
            "stability": source.stability,
            "frequency": source.frequency,
            "expected_amount": str(source.default_amount) if source.default_amount else None,
            "default_account_id": str(source.default_account_id) if source.default_account_id else None,
            "default_category_id": str(source.default_category_id) if source.default_category_id else None,
            "default_currency": source.default_currency,
            "is_active": source.is_active,
            "created_at": source.created_at.isoformat() if source.created_at else None,
        }
