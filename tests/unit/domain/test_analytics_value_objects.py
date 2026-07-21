"""Unit tests for analytics value objects."""

from __future__ import annotations

import pytest

from app.domain.analytics.value_objects import (
    AnalyticsDimension,
    AnalyticsPeriod,
    HeatmapGranularity,
)


class TestAnalyticsPeriod:
    def test_valid_periods(self):
        assert str(AnalyticsPeriod("daily")) == "daily"
        assert str(AnalyticsPeriod("MONTHLY")) == "monthly"
        assert AnalyticsPeriod("yearly").name == "Anual"

    def test_invalid_period(self):
        with pytest.raises(ValueError, match="no soportado"):
            AnalyticsPeriod("invalid")


class TestAnalyticsDimension:
    def test_valid_dimensions(self):
        assert str(AnalyticsDimension("category")) == "category"
        assert AnalyticsDimension("account").name == "Por Cuenta"

    def test_invalid_dimension(self):
        with pytest.raises(ValueError, match="no soportad"):
            AnalyticsDimension("unknown")


class TestHeatmapGranularity:
    def test_valid_granularities(self):
        assert str(HeatmapGranularity("day_of_week_month")) == "day_of_week_month"
        assert HeatmapGranularity("category_month").name == "Categoría × Mes"  # noqa: RUF001

    def test_invalid_granularity(self):
        with pytest.raises(ValueError, match="no soportad"):
            HeatmapGranularity("hour_minute")
