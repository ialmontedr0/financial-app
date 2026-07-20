"""Domain value objects for Incomes module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


# ======================================================================
# Vocabulary
# ======================================================================

INCOME_TYPES: dict[str, str] = {
    "salary": "Salario",
    "freelance": "Freelance",
    "business": "Negocio",
    "investment": "Inversiones",
    "rental": "Alquileres",
    "refund": "Reembolsos",
    "gift": "Regalos",
    "bonus": "Bonificaciones",
    "commission": "Comisiones",
    "other": "Otros",
}

INCOME_STATUSES: dict[str, str] = {
    "pending": "Pendiente",
    "confirmed": "Confirmado",
    "received": "Recibido",
    "projected": "Proyectado",
    "cancelled": "Cancelado",
}

INCOME_STABILITY: dict[str, str] = {
    "fixed": "Fijo",
    "variable": "Variable",
    "irregular": "Irregular",
    "one_time": "Unico",
}

SCHEDULE_STATUSES: dict[str, str] = {
    "projected": "Proyectado",
    "expected": "Esperado",
    "received": "Recibido",
    "overdue": "Vencido",
    "cancelled": "Cancelado",
}

PROJECTION_METHODS: dict[str, str] = {
    "fixed": "Monto Fijo",
    "average_3m": "Promedio 3 Meses",
    "average_6m": "Promedio 6 Meses",
    "average_12m": "Promedio 12 Meses",
    "trend": "Tendencia Lineal",
    "manual": "Manual",
}


# ======================================================================
# Value Objects
# ======================================================================

@dataclass(frozen=True)
class IncomeType:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(INCOME_TYPES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Tipo de ingreso no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return INCOME_TYPES.get(self.value, self.value)


@dataclass(frozen=True)
class IncomeStatus:
    value: str
    _VALID_STATUSES: ClassVar[frozenset[str]] = frozenset(INCOME_STATUSES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_STATUSES:
            supported = ", ".join(sorted(self._VALID_STATUSES))
            raise ValueError(f"Estado de ingreso no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return INCOME_STATUSES.get(self.value, self.value)


@dataclass(frozen=True)
class IncomeStability:
    value: str
    _VALID_STABILITY: ClassVar[frozenset[str]] = frozenset(INCOME_STABILITY.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_STABILITY:
            supported = ", ".join(sorted(self._VALID_STABILITY))
            raise ValueError(f"Estabilidad no soportada: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return INCOME_STABILITY.get(self.value, self.value)


@dataclass(frozen=True)
class ScheduleStatus:
    value: str
    _VALID_STATUSES: ClassVar[frozenset[str]] = frozenset(SCHEDULE_STATUSES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_STATUSES:
            supported = ", ".join(sorted(self._VALID_STATUSES))
            raise ValueError(f"Estado de programacion no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return SCHEDULE_STATUSES.get(self.value, self.value)


@dataclass(frozen=True)
class ProjectionMethod:
    value: str
    _VALID_METHODS: ClassVar[frozenset[str]] = frozenset(PROJECTION_METHODS.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_METHODS:
            supported = ", ".join(sorted(self._VALID_METHODS))
            raise ValueError(f"Metodo de proyeccion no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return PROJECTION_METHODS.get(self.value, self.value)
