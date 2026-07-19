"""Domain value objects for Financial Accounts."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import ClassVar

# ==============================================================================
# Account Types
# ==============================================================================
ACCOUNT_TYPES: dict[str, str] = {
    "bank": "Cuenta Bancaria",
    "cash": "Efectivo",
    "savings": "Cuenta de Ahorro",
    "checking": "Cuenta Corriente",
    "wallet": "Billetera Digital",
    "crypto": "Criptomonedas",
}


# ==============================================================================
# Account Statuses
# ==============================================================================
ACCOUNT_STATUSES: dict[str, str] = {
    "active": "Activa",
    "inactive": "Inactiva",
    "archived": "Archivada",
    "frozen": "Congelada",
}


@dataclass(frozen=True)
class AccountType:
    """Value object para tipo de cuenta validado."""

    value: str

    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(ACCOUNT_TYPES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Tipo de cuenta no soportado: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        """Nombre legible por humano."""
        return ACCOUNT_TYPES.get(self.value, self.value)


@dataclass(frozen=True)
class AccountStatus:
    """Value object para estado de cuenta validado."""

    value: str

    _VALID_STATUSES: ClassVar[frozenset[str]] = frozenset(ACCOUNT_STATUSES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_STATUSES:
            supported = ", ".join(sorted(self._VALID_STATUSES))
            raise ValueError(
                f"Estado de cuenta no soportado: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        """Nombre legible por humano."""
        return ACCOUNT_STATUSES.get(self.value, self.value)


@dataclass(frozen=True)
class AccountBalance:
    """Value object para balance de cuenta con validacion monetaria."""

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        from app.domain.users.value_objects import CurrencyCode

        CurrencyCode(self.currency)

        if not isinstance(self.amount, Decimal):
            try:
                object.__setattr__(self, "amount", Decimal(str(self.amount)))
            except (InvalidOperation, ValueError):
                raise ValueError(f"Balance invalido: {self.amount}")

        if self.amount.as_tuple().exponent > 4:
            raise ValueError(
                f"Balance con demasiados decimales: {self.amount}. Maximo 4 decimales."
            )

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"

    def __add__(self, other: AccountBalance) -> AccountBalance:
        if self.currency != other.currency:
            raise ValueError(
                f"No se pueden sumar montos en diferentes monedas: {self.currency} y {other.currency}"
            )
        return AccountBalance(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: AccountBalance) -> AccountBalance:
        if self.currency != other.currency:
            raise ValueError(
                f"No se pueden restar montos en diferentes monedas: {self.currency} y {other.currency}"
            )
        return AccountBalance(amount=self.amount - other.amount, currency=self.currency)
