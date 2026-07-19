"""Domain value objects for Wallets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

WALLET_TYPES: dict[str, str] = {
    "personal": "Personal",
    "business": "Negocio",
    "savings": "Ahorro",
    "investment": "Inversion",
    "daily": "Uso Diario",
    "emergency": "Fondo de Emergencia",
}

WALLET_STATUSES: dict[str, str] = {
    "active": "Activa",
    "archived": "Archivada",
}

LIQUIDITY_LEVELS: dict[str, str] = {
    "high": "Alta - Acceso inmediato",
    "medium": "Media - Acceso en 1-3 dias",
    "low": "Baja - Acceso variable",
    "mixed": "Mixta - Multiples niveles",
}


@dataclass(frozen=True)
class WalletType:
    """Value object para tipo de wallet validado."""

    value: str

    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(WALLET_TYPES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(
                f"Tipo de wallet no soportado: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return WALLET_TYPES.get(self.value, self.value)


@dataclass(frozen=True)
class WalletStatus:
    """Value object para estado de wallet validado."""

    value: str

    _VALID_STATUSES: ClassVar[frozenset[str]] = frozenset(WALLET_STATUSES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_STATUSES:
            supported = ", ".join(sorted(self._VALID_STATUSES))
            raise ValueError(
                f"Estado de wallet no soportado: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return WALLET_STATUSES.get(self.value, self.value)


@dataclass(frozen=True)
class LiquidityLevel:
    """Value object para nivel de liquidez."""

    value: str

    _VALID_LEVELS: ClassVar[frozenset[str]] = frozenset(LIQUIDITY_LEVELS.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_LEVELS:
            supported = ", ".join(sorted(self._VALID_LEVELS))
            raise ValueError(
                f"Nivel de liquidez no soportado: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return LIQUIDITY_LEVELS.get(self.value, self.value)
