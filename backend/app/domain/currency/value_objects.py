"""Domain value objects for multi-currency operations.

Pure business rules for money and currency pairs. No I/O here: exchange
rate *values* are provided by infrastructure, conversion arithmetic lives
here so it can be unit-tested without a database.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import ClassVar

from app.domain.users.value_objects import CurrencyCode

# Maximum decimal places used for converted monetary amounts.
MONEY_PRECISION: int = 4
MONEY_QUANTUM: Decimal = Decimal("1").scaleb(-MONEY_PRECISION)


def _to_decimal(value: Decimal | int | float | str, field: str) -> Decimal:
    """Coerce a raw value to Decimal raising a clear error on failure."""
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} invalido: {value}") from None


def _validate_currency(code: str) -> str:
    """Normalize and validate an ISO 4217 currency code."""
    return CurrencyCode(code).code


def round_money(amount: Decimal) -> Decimal:
    """Round a monetary amount to the canonical precision (half-up)."""
    return amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def format_rate(rate: Decimal) -> str:
    """Format a rate without trailing zeros and avoiding scientific notation."""
    return format(rate.normalize(), "f")


@dataclass(frozen=True)
class CurrencyPair:
    """Un par de divisas fuente->destino con validacion ISO 4217."""

    source: str
    target: str

    _SAME_CURRENCY: ClassVar[str] = "same"

    def __post_init__(self) -> None:
        source = _validate_currency(self.source)
        target = _validate_currency(self.target)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "target", target)

    @property
    def is_same_currency(self) -> bool:
        """True cuando origen y destino son la misma divisa."""
        return self.source == self.target

    @property
    def inverse(self) -> CurrencyPair:
        """El par inverso (destino->origen)."""
        return CurrencyPair(source=self.target, target=self.source)

    def __str__(self) -> str:
        if self.is_same_currency:
            return self._SAME_CURRENCY
        return f"{self.source}->{self.target}"


@dataclass(frozen=True)
class Money:
    """Cantidad monetaria inalterable ligada a una divisa."""

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        currency = _validate_currency(self.currency)
        object.__setattr__(self, "currency", currency)
        object.__setattr__(self, "amount", _to_decimal(self.amount, "Monto"))

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(
                f"No se pueden sumar montos en diferentes monedas: "
                f"{self.currency} y {other.currency}"
            )
        return Money(amount=round_money(self.amount + other.amount), currency=self.currency)

    def __sub__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(
                f"No se pueden restar montos en diferentes monedas: "
                f"{self.currency} y {other.currency}"
            )
        return Money(amount=round_money(self.amount - other.amount), currency=self.currency)

    def convert(self, rate: Decimal, to_currency: str) -> Money:
        """Convierte esta cantidad a otra divisa usando la tasa dada.

        ``rate`` expresa el valor de 1 unidad de ``self.currency`` en
        ``to_currency``. La conversion de moneda identica es la identidad.
        """
        target = _validate_currency(to_currency)
        if self.currency == target:
            return Money(amount=round_money(self.amount), currency=target)
        rate_decimal = _to_decimal(rate, "Tasa de cambio")
        if rate_decimal <= 0:
            raise ValueError(f"Tasa de cambio invalida: {rate}. Debe ser positiva.")
        return Money(
            amount=round_money(self.amount * rate_decimal),
            currency=target,
        )
