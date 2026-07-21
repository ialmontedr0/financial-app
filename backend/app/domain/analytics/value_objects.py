"""Analytics domain value objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

ANALYTICS_PERIODS = {
    "daily": "Diario",
    "weekly": "Semanal",
    "monthly": "Mensual",
    "quarterly": "Trimestral",
    "yearly": "Anual",
}

ANALYTICS_DIMENSIONS = {
    "category": "Por Categoría",
    "account": "Por Cuenta",
    "type": "Por Tipo",
    "day_of_week": "Por Día de la Semana",
    "month": "Por Mes",
    "hour": "Por Hora",
}

HEATMAP_GRANULARITIES = {
    "day_of_week_month": "Día de Semana × Mes",  # noqa: RUF001
    "day_of_week_hour": "Día de Semana × Hora",  # noqa: RUF001
    "category_month": "Categoría × Mes",  # noqa: RUF001
}


@dataclass(frozen=True)
class AnalyticsPeriod:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(ANALYTICS_PERIODS.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(
                f"Período analítico no soportado: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return ANALYTICS_PERIODS.get(self.value, self.value)


@dataclass(frozen=True)
class AnalyticsDimension:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(ANALYTICS_DIMENSIONS.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(
                f"Dimensión analítica no soportada: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return ANALYTICS_DIMENSIONS.get(self.value, self.value)


@dataclass(frozen=True)
class HeatmapGranularity:
    value: str
    _VALID_TYPES: ClassVar[frozenset[str]] = frozenset(HEATMAP_GRANULARITIES.keys())

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        if normalized not in self._VALID_TYPES:
            supported = ", ".join(sorted(self._VALID_TYPES))
            raise ValueError(
                f"Granularidad de mapa de calor no soportada: {self.value}. Soportado: {supported}"
            )
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @property
    def name(self) -> str:
        return HEATMAP_GRANULARITIES.get(self.value, self.value)
