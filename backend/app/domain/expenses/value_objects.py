from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

EXPENSE_METHODS: dict[str, str] = {
    "manual": "Manual",
    "template": "Deste template",
    "split": "Dividido",
    "import": "Importado",
    "auto": "Automatico",
}

EXPENSE_PRIORITIES: dict[str, str] = {
    "low": "Baja",
    "normal": "Normal",
    "high": "Alta",
    "critical": "Critica",
}

SERVICE_FREQUENCIES: dict[str, str] = {
    "monthly": "Mensual",
    "bimonthly": "Bimensual",
    "quarterly": "Trimestral",
    "semiannual": "Semestral",
    "yearly": "Anual",
}

SUBSCRIPTION_STATUSES: dict[str, str] = {
    "active": "Activa",
    "paused": "Pausada",
    "cancelled": "Cancelada",
    "trial": "Prueba",
    "expired": "Expirada",
}

PAYMENT_STATUSES: dict[str, str] = {
    "pending": "Pendiente",
    "paid": "Pagado",
    "overdue": "Vencido",
    "partial": "Parcial",
    "waived": "Excento",
}


@dataclass(frozen=True)
class ExpenseMethod:
    value: str
    _VALID: ClassVar[frozenset[str]] = frozenset(EXPENSE_METHODS.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID:
            supported = ", ".join(sorted(self._VALID))
            raise ValueError(f"Metodo de gasto no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return EXPENSE_METHODS.get(self.value, self.value)


@dataclass(frozen=True)
class ExpensePriority:
    value: str
    _VALID: ClassVar[frozenset[str]] = frozenset(EXPENSE_PRIORITIES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID:
            supported = ", ".join(sorted(self._VALID))
            raise ValueError(f"Prioridad no soportada: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return EXPENSE_PRIORITIES.get(self.value, self.value)


@dataclass(frozen=True)
class ServiceFrequency:
    value: str
    _VALID: ClassVar[frozenset[str]] = frozenset(SERVICE_FREQUENCIES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID:
            supported = ", ".join(sorted(self._VALID))
            raise ValueError(
                f"Frecuencia de servicio no soportada: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return SERVICE_FREQUENCIES.get(self.value, self.value)


@dataclass(frozen=True)
class SubscriptionStatus:
    value: str
    _VALID: ClassVar[frozenset[str]] = frozenset(SUBSCRIPTION_STATUSES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID:
            supported = ", ".join(sorted(self._VALID))
            raise ValueError(
                f"Estado de suscripcion no soportado: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return SUBSCRIPTION_STATUSES.get(self.value, self.value)


@dataclass(frozen=True)
class PaymentStatus:
    value: str
    _VALID: ClassVar[frozenset[str]] = frozenset(PAYMENT_STATUSES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID:
            supported = ", ".join(sorted(self._VALID))
            raise ValueError(f"Estado de pago no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return PAYMENT_STATUSES.get(self.value, self.value)
