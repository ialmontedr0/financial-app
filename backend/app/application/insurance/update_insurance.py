"""Update an insurance policy."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.insurance.value_objects import (
    InsuranceStatus,
    InsuranceType,
    PremiumFrequency,
)
from app.infrastructure.repositories.insurance_repository import InsuranceRepository
from app.middleware.error_handler import NotFoundError, ValidationError

logger = structlog.get_logger()


class UpdateInsuranceUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InsuranceRepository(session)

    async def execute(
        self, user_id: uuid.UUID, insurance_id: uuid.UUID, fields: dict[str, Any]
    ) -> dict[str, Any]:
        insurance = await self._repo.get_insurance(insurance_id, user_id)
        if insurance is None:
            raise NotFoundError("Seguro no encontrado")

        updates: dict[str, Any] = {}

        if "name" in fields and fields["name"] is not None:
            name = fields["name"].strip()
            if not name:
                raise ValidationError("El nombre del seguro es requerido")
            if len(name) > 200:
                raise ValidationError("El nombre no puede exceder 200 caracteres")
            updates["name"] = name

        if "type" in fields and fields["type"] is not None:
            try:
                updates["type"] = InsuranceType(fields["type"]).value
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc

        if "status" in fields and fields["status"] is not None:
            try:
                updates["status"] = InsuranceStatus(fields["status"]).value
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc

        if "premium_frequency" in fields and fields["premium_frequency"] is not None:
            try:
                updates["premium_frequency"] = PremiumFrequency(fields["premium_frequency"]).value
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc

        for field in ("provider", "policy_number", "notes"):
            if field in fields:
                updates[field] = fields[field]

        if "start_date" in fields and fields["start_date"] is not None:
            updates["start_date"] = date.fromisoformat(fields["start_date"])

        if "end_date" in fields:
            updates["end_date"] = (
                date.fromisoformat(fields["end_date"]) if fields["end_date"] else None
            )

        if "premium_amount" in fields and fields["premium_amount"] is not None:
            premium = Decimal(str(fields["premium_amount"]))
            if premium <= 0:
                raise ValidationError("El monto de la prima debe ser mayor a 0")
            updates["premium_amount"] = premium

        if "coverage_amount" in fields:
            if fields["coverage_amount"] is None:
                updates["coverage_amount"] = None
            else:
                coverage = Decimal(str(fields["coverage_amount"]))
                if coverage < 0:
                    raise ValidationError("El monto de cobertura no puede ser negativo")
                updates["coverage_amount"] = coverage

        new_start = updates.get("start_date", insurance.start_date)
        new_end = updates.get("end_date", insurance.end_date)
        if new_end and new_end < new_start:
            raise ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio")

        if updates:
            insurance = await self._repo.update_insurance(insurance, **updates)

        return {
            "id": str(insurance.id),
            "name": insurance.name,
            "type": insurance.type,
            "provider": insurance.provider,
            "policy_number": insurance.policy_number,
            "status": insurance.status,
            "start_date": insurance.start_date.isoformat(),
            "end_date": insurance.end_date.isoformat() if insurance.end_date else None,
            "coverage_amount": float(insurance.coverage_amount)
            if insurance.coverage_amount
            else None,
            "premium_amount": float(insurance.premium_amount),
            "premium_frequency": insurance.premium_frequency,
            "notes": insurance.notes,
        }
