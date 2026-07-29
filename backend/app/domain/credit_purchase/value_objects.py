from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

CREDIT_PURCHASE_STATUSES = {
    "active": "Activa",
    "completed": "Completada",
    "cancelled": "Cancelada",
    "defaulted": "En Incumplimiento",
}

INSTALLMENT_FREQUENCIES = {
    "weekly": "Semanal",
    "biweekly": "Quincenal",
    "monthly": "Mensual",
    "quarterly": "Trimestral",
    "quadrimensual": "Cuatrimestral",
    "semestral": "Semestral",
    "annual": "Anual",
}

INSTALLMENT_STATUSES = {
    "pending": "Pendiente",
    "paid": "Pagada",
    "late": "Atrasada",
}

FREQUENCY_MONTHS: dict[str, Decimal] = {
    "weekly": Decimal("0.230137"),
    "biweekly": Decimal("0.460274"),
    "monthly": Decimal("1"),
    "quarterly": Decimal("3"),
    "quadrimensual": Decimal("4"),
    "semestral": Decimal("6"),
    "annual": Decimal("12"),
}


@dataclass(frozen=True)
class CreditPurchaseStatus:
    value: str
    _VALID: ClassVar[frozenset[str]] = frozenset(CREDIT_PURCHASE_STATUSES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID:
            raise ValueError(f"Estado no soportado: {self.value}")
        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True)
class InstallmentFrequency:
    value: str
    _VALID: ClassVar[frozenset[str]] = frozenset(INSTALLMENT_FREQUENCIES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID:
            raise ValueError(f"Frecuencia no soportada: {self.value}")
        object.__setattr__(self, "value", normalized)

    @property
    def months_multiplier(self) -> Decimal:
        return FREQUENCY_MONTHS.get(self.value, Decimal("1"))


@dataclass(frozen=True)
class InstallmentStatus:
    value: str
    _VALID: ClassVar[frozenset[str]] = frozenset(INSTALLMENT_STATUSES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID:
            raise ValueError(f"Estado de cuota no soportado: {self.value}")
        object.__setattr__(self, "value", normalized)
