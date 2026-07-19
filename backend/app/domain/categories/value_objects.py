"""Domain value objects for Categories."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

# ==============================================================================
# Category Types (direction of money flow)
# ==============================================================================
CATEGORY_TYPES: dict[str, str] = {
    "expense": "Gasto",
    "income": "Ingreso",
    "transfer": "Transferencia",
    "adjustment": "Ajuste",
}


# ==============================================================================
# Category Scope (who owns the category)
# ==============================================================================
CATEGORY_SCOPES: dict[str, str] = {
    "system": "Del Sistema",
    "user": "Del Usuario",
}


# ==============================================================================
# Rule Priority Levels
# ==============================================================================
RULE_PRIORITIES: dict[str, str] = {
    "critical": "Critica — Se evalua primero",
    "high": "Alta",
    "normal": "Normal",
    "low": "Baja",
}


# ==============================================================================
# Pattern Types for rules
# ==============================================================================
PATTERN_TYPES: dict[str, str] = {
    "keyword": "Palabras clave (OR)",
    "regex": "Expresion regular",
    "amount_range": "Rango de monto",
    "merchant_exact": "Nombre exacto del merchant",
}


@dataclass(frozen=True)
class CategoryType:
    """Value object para tipo de categoria (expense/income/transfer/adjustment)."""

    value: str

    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(CATEGORY_TYPES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(
                f"Tipo de categoria no soportado: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return CATEGORY_TYPES.get(self.value, self.value)


@dataclass(frozen=True)
class CategoryScope:
    """Value object para scope de categoria (system/user)."""

    value: str

    _VALID_SCOPES: ClassVar[frozenset[str]] = frozenset(CATEGORY_SCOPES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_SCOPES:
            supported = ", ".join(sorted(self._VALID_SCOPES))
            raise ValueError(
                f"Scope de categoria no soportado: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return CATEGORY_SCOPES.get(self.value, self.value)


@dataclass(frozen=True)
class PatternType:
    """Value object para tipo de patron de regla."""

    value: str

    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(PATTERN_TYPES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(
                f"Tipo de patron no soportado: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return PATTERN_TYPES.get(self.value, self.value)
