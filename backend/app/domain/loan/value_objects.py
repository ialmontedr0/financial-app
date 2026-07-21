from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

LOAN_TYPES = {
    "personal": "Préstamo Personal",
    "mortgage": "Hipotecario",
    "auto": "Auto",
    "student": "Estudiantil",
    "business": "Empresarial",
    "personal_line": "Línea de Crédito",
    "payday": "Préstamo de Nómina",
    "microloan": "Microcrédito",
    "consolidation": "Consolidación de Deuda",
}

LOAN_STATUSES = {
    "pending": "Pendiente",
    "active": "Activo",
    "paid_off": "Pagado",
    "defaulted": "En Incumplimiento",
    "refinanced": "Refinanciado",
    "suspended": "Suspendido",
    "cancelled": "Cancelado",
}

PAYMENT_FREQUENCIES = {
    "monthly": "Mensual",
    "bi_weekly": "Quincenal",
    "weekly": "Semanal",
}

INTEREST_TYPES = {
    "fixed": "Fijo",
    "variable": "Variable",
    "mixed": "Mixto",
}

PAYMENT_METHODS = {
    "bank_transfer": "Transferencia Bancaria",
    "cash": "Efectivo",
    "auto_debit": "Débito Automático",
    "check": "Cheque",
    "online": "En Línea",
    "mobile": "Móvil",
}

PAYMENT_STATUS = {
    "pending": "Pendiente",
    "completed": "Completado",
    "failed": "Fallido",
    "reversed": "Revertido",
}


@dataclass(frozen=True)
class LoanType:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(LOAN_TYPES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Tipo de préstamo no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return LOAN_TYPES.get(self.value, self.value)


@dataclass(frozen=True)
class LoanStatus:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(LOAN_STATUSES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(
                f"Estado de préstamo no soportado: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return LOAN_STATUSES.get(self.value, self.value)


@dataclass(frozen=True)
class PaymentFrequency:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(PAYMENT_FREQUENCIES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(
                f"Frecuencia de pago no soportada: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return PAYMENT_FREQUENCIES.get(self.value, self.value)

    @property
    def payments_per_year(self) -> int:
        mapping = {"monthly": 12, "bi_weekly": 26, "weekly": 52}
        return mapping[self.value]


@dataclass(frozen=True)
class InterestType:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(INTEREST_TYPES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Tipo de interés no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return INTEREST_TYPES.get(self.value, self.value)


@dataclass(frozen=True)
class PaymentMethod:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(PAYMENT_METHODS.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Método de pago no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return PAYMENT_METHODS.get(self.value, self.value)


@dataclass(frozen=True)
class LoanPaymentStatus:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(PAYMENT_STATUS.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Estado de pago no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return PAYMENT_STATUS.get(self.value, self.value)
