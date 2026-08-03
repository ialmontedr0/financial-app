"""Insurance domain value objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

INSURANCE_TYPES = {
    "life": "Seguro de Vida",
    "health": "Seguro de Salud",
    "auto": "Seguro de Auto",
    "home": "Seguro de Hogar",
    "travel": "Seguro de Viaje",
    "disability": "Seguro de Discapacidad",
    "other": "Otro",
}

INSURANCE_STATUSES = {
    "active": "Activo",
    "cancelled": "Cancelado",
    "expired": "Expirado",
    "pending": "Pendiente",
}

PREMIUM_FREQUENCIES = {
    "monthly": "Mensual",
    "quarterly": "Trimestral",
    "semi_annual": "Semestral",
    "annual": "Anual",
}

PREMIUM_STATUSES = {
    "pending": "Pendiente",
    "paid": "Pagado",
    "overdue": "Vencido",
    "cancelled": "Cancelado",
}

PAYMENT_METHODS = {
    "bank_transfer": "Transferencia Bancaria",
    "cash": "Efectivo",
    "auto_debit": "Débito Automático",
    "check": "Cheque",
    "online": "En Línea",
    "mobile": "Móvil",
}


@dataclass(frozen=True)
class InsuranceType:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(INSURANCE_TYPES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Valor no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return INSURANCE_TYPES.get(self.value, self.value)


@dataclass(frozen=True)
class InsuranceStatus:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(INSURANCE_STATUSES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Valor no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return INSURANCE_STATUSES.get(self.value, self.value)


@dataclass(frozen=True)
class PremiumFrequency:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(PREMIUM_FREQUENCIES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Valor no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return PREMIUM_FREQUENCIES.get(self.value, self.value)

    @property
    def payments_per_year(self) -> int:
        mapping = {"monthly": 12, "quarterly": 4, "semi_annual": 2, "annual": 1}
        return mapping[self.value]


@dataclass(frozen=True)
class PremiumStatus:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(PREMIUM_STATUSES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Valor no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return PREMIUM_STATUSES.get(self.value, self.value)


@dataclass(frozen=True)
class PaymentMethod:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(PAYMENT_METHODS.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Valor no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return PAYMENT_METHODS.get(self.value, self.value)
