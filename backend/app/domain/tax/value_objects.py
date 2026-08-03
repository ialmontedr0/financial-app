"""Tax domain value objects."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import ClassVar

MIN_TAX_YEAR = 1900
MAX_TAX_YEAR = 2200


@dataclass(frozen=True)
class TaxYear:
    """A valid fiscal year."""

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise ValueError("El año fiscal debe ser un número entero")
        if self.value < MIN_TAX_YEAR or self.value > MAX_TAX_YEAR:
            raise ValueError(
                f"Año fiscal no válido: {self.value}. Debe estar entre {MIN_TAX_YEAR} y {MAX_TAX_YEAR}"
            )

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class TaxCategoryName:
    """A non-empty tax category name."""

    value: str
    _MAX_LENGTH: ClassVar[int] = 200

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise ValueError("El nombre de la categoría es requerido")
        if len(normalized) > self._MAX_LENGTH:
            raise ValueError(f"El nombre no puede exceder {self._MAX_LENGTH} caracteres")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TaxDeductionDescription:
    """A non-empty tax deduction description."""

    value: str
    _MAX_LENGTH: ClassVar[int] = 500

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise ValueError("La descripción de la deducción es requerida")
        if len(normalized) > self._MAX_LENGTH:
            raise ValueError(f"La descripción no puede exceder {self._MAX_LENGTH} caracteres")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class MoneyAmount:
    """A positive monetary amount."""

    value: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal):
            raise ValueError("El monto debe ser un valor decimal")
        if self.value < 0:
            raise ValueError("El monto no puede ser negativo")
        object.__setattr__(
            self, "value", self.value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

    def __str__(self) -> str:
        return str(self.value)
