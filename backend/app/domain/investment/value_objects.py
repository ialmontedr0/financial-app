"""Investment domain value objects."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

ASSET_TYPES = {
    "stock": "Accion",
    "bond": "Bono",
    "etf": "ETF",
    "crypto": "Criptomoneda",
    "mutual_fund": "Fondo Mutuo",
    "real_estate": "Bien Raiz",
    "commodity": "Materia Prima",
}

INVESTMENT_TX_TYPES = {
    "buy": "Compra",
    "sell": "Venta",
    "dividend": "Dividendo",
    "fee": "Comision",
}

CURRENCIES = {
    "USD": "USD",
    "EUR": "EUR",
    "MXN": "MXN",
    "DOP": "DOP",
    "COP": "COP",
}


@dataclass(frozen=True)
class AssetType:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(ASSET_TYPES.keys())

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
        return ASSET_TYPES.get(self.value, self.value)


@dataclass(frozen=True)
class InvestmentTxType:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(INVESTMENT_TX_TYPES.keys())

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
        return INVESTMENT_TX_TYPES.get(self.value, self.value)


@dataclass(frozen=True)
class Currency:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(CURRENCIES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.upper().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(f"Moneda no soportada: {self.value}. Soportado: {supported}")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PortfolioSummary:
    total_value: Decimal
    total_cost: Decimal
    gain_loss: Decimal
    gain_loss_percent: Decimal
    asset_allocation: dict[str, Decimal]

    def as_dict(self) -> dict[str, object]:
        return {
            "total_value": float(self.total_value.quantize(Decimal("0.01"))),
            "total_cost": float(self.total_cost.quantize(Decimal("0.01"))),
            "gain_loss": float(self.gain_loss.quantize(Decimal("0.01"))),
            "gain_loss_percent": float(self.gain_loss_percent.quantize(Decimal("0.01"))),
            "asset_allocation": {
                key: float(value.quantize(Decimal("0.01")))
                for key, value in self.asset_allocation.items()
            },
        }
