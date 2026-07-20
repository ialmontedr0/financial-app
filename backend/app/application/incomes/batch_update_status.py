"""Use case: Batch update income statuses."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class BatchUpdateStatusUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncomeRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        income_ids: list[str],
        status: str,
    ) -> dict:
        from app.middleware.error_handler import ValidationError

        valid_statuses = {"pending", "confirmed", "received", "projected", "cancelled"}
        if status not in valid_statuses:
            raise ValidationError(f"status no valido: {status}. Soportado: {', '.join(sorted(valid_statuses))}")

        if not income_ids:
            raise ValidationError("income_ids no puede estar vacio")

        updated = []
        not_found = []

        import uuid

        for income_id_str in income_ids:
            income_id = uuid.UUID(income_id_str)
            income = await self._repo.get_income_by_id(income_id, user_id)
            if income is None:
                not_found.append(income_id_str)
                continue

            await self._repo.update_income(income_id, user_id, income_status=status)
            updated.append(income_id_str)

        return {
            "updated_count": len(updated),
            "not_found_count": len(not_found),
            "updated_ids": updated,
            "not_found_ids": not_found,
        }
