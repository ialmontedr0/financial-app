"""Create a new insurance policy."""

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
from app.middleware.error_handler import ValidationError

logger = structlog.get_logger()


class CreateInsuranceUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InsuranceRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        name: str,
        type: str,  # noqa: A002
        start_date: date,
        premium_amount: float | Decimal,
        premium_frequency: str = "monthly",
        provider: str | None = None,
        policy_number: str | None = None,
        status: str = "active",
        end_date: date | None = None,
        coverage_amount: float | Decimal | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        try:
            validated_type = InsuranceType(type)
            validated_status = InsuranceStatus(status)
            validated_frequency = PremiumFrequency(premium_frequency)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        if not name or not name.strip():
            raise ValidationError("El nombre del seguro es requerido")
        if len(name.strip()) > 200:
            raise ValidationError("El nombre no puede exceder 200 caracteres")

        try:
            premium = Decimal(str(premium_amount))
        except Exception as exc:  # pragma: no cover
            raise ValidationError("El monto de la prima no es válido") from exc
        if premium <= 0:
            raise ValidationError("El monto de la prima debe ser mayor a 0")

        coverage = Decimal(str(coverage_amount)) if coverage_amount is not None else None
        if coverage is not None and coverage < 0:
            raise ValidationError("El monto de cobertura no puede ser negativo")

        if end_date and end_date < start_date:
            raise ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio")

        insurance = await self._repo.create_insurance(
            user_id=user_id,
            name=name.strip(),
            type=validated_type.value,
            provider=provider,
            policy_number=policy_number,
            status=validated_status.value,
            start_date=start_date,
            end_date=end_date,
            coverage_amount=coverage,
            premium_amount=premium,
            premium_frequency=validated_frequency.value,
            notes=notes,
        )

        logger.info("insurance_created", insurance_id=str(insurance.id), type=type)
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
            "created_at": insurance.created_at.isoformat() if insurance.created_at else None,
        }
