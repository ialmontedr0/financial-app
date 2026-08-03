"""Plaid domain value objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

PLAID_ENVIRONMENTS = {
    "sandbox": "Sandbox",
    "development": "Desarrollo",
    "production": "Producción",
}

PLAID_PRODUCTS = {
    "transactions": "Transacciones",
    "auth": "Autenticación de cuentas",
    "identity": "Identidad",
}

PLAID_ITEM_STATUSES = {
    "connected": "Conectado",
    "disconnected": "Desconectado",
    "error": "Error",
}


@dataclass(frozen=True)
class PlaidEnvironment:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(PLAID_ENVIRONMENTS.keys())

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
        return PLAID_ENVIRONMENTS.get(self.value, self.value)


@dataclass(frozen=True)
class PlaidItemStatus:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(PLAID_ITEM_STATUSES.keys())

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
        return PLAID_ITEM_STATUSES.get(self.value, self.value)
