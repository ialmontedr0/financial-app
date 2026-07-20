"""Domain value objects for Transactions."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from typing import ClassVar

TRANSACTION_TYPES: dict[str, str] = {
    "income": "Ingreso",
    "expense": "Gasto",
    "transfer": "Transferencia",
    "adjustment": "Ajuste",
}

TRANSACTION_STATUSES: dict[str, str] = {
    "draft": "Borrador",
    "pending": "Pendiente",
    "completed": "Completada",
    "cancelled": "Cancelada",
    "failed": "Fallida",
}

TRANSACTION_SOURCES: dict[str, str] = {
    "manual": "Manual",
    "import": "Importacion",
    "recurring": "Recurrente",
    "api": "API",
    "ocr": "OCR",
}

RECURRENCE_FREQUENCIES: dict[str, str] = {
    "daily": "Diaria",
    "weekly": "Semanal",
    "biweekly": "Quincenal",
    "monthly": "Mensual",
    "quarterly": "Trimestral",
    "yearly": "Anual",
}

AUDIT_ACTIONS: dict[str, str] = {
    "created": "Creada",
    "updated": "Actualizada",
    "deleted": "Eliminada",
    "restored": "Restaurada",
}


@dataclass(frozen=True)
class TransactionType:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(TRANSACTION_TYPES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Tipo de transaccion no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return TRANSACTION_TYPES.get(self.value, self.value)


@dataclass(frozen=True)
class TransactionStatus:
    value: str
    _VALID_STATUSES: ClassVar[frozenset[str]] = frozenset(TRANSACTION_STATUSES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_STATUSES:
            supported = ", ".join(sorted(self._VALID_STATUSES))
            raise ValueError(f"Estado no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return TRANSACTION_STATUSES.get(self.value, self.value)


@dataclass(frozen=True)
class TransactionSource:
    value: str
    _VALID_SOURCES: ClassVar[frozenset[str]] = frozenset(TRANSACTION_SOURCES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_SOURCES:
            supported = ", ".join(sorted(self._VALID_SOURCES))
            raise ValueError(f"Origen no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return TRANSACTION_SOURCES.get(self.value, self.value)


@dataclass(frozen=True)
class RecurrenceFrequency:
    value: str
    _VALID_FREQS: ClassVar[frozenset[str]] = frozenset(RECURRENCE_FREQUENCIES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_FREQS:
            supported = ", ".join(sorted(self._VALID_FREQS))
            raise ValueError(f"Frecuencia no soportada: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return RECURRENCE_FREQUENCIES.get(self.value, self.value)

    def calculate_next_date(self, current: date, interval: int = 1) -> date:
        if self.value == "daily":
            return current + timedelta(days=interval)
        elif self.value == "weekly":
            return current + timedelta(weeks=interval)
        elif self.value == "biweekly":
            return current + timedelta(weeks=2 * interval)
        elif self.value in ("monthly", "quarterly", "yearly"):
            multipliers = {"monthly": 1, "quarterly": 3, "yearly": 12}
            months = interval * multipliers[self.value]
            month = current.month + months
            year = current.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(current.day, calendar.monthrange(year, month)[1])
            return date(year, month, day)
        return current + timedelta(days=1)


@dataclass(frozen=True)
class AuditAction:
    value: str
    _VALID_ACTIONS: ClassVar[frozenset[str]] = frozenset(AUDIT_ACTIONS.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_ACTIONS:
            supported = ", ".join(sorted(self._VALID_ACTIONS))
            raise ValueError(f"Accion no soportada: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return AUDIT_ACTIONS.get(self.value, self.value)
