"""Unit tests for tax value objects."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.tax.value_objects import (
    MoneyAmount,
    TaxCategoryName,
    TaxDeductionDescription,
    TaxYear,
)


class TestTaxYear:
    def test_valid_year(self):
        assert TaxYear(2026).value == 2026

    def test_invalid_year_too_low(self):
        with pytest.raises(ValueError, match="no válido"):
            TaxYear(1800)

    def test_invalid_year_too_high(self):
        with pytest.raises(ValueError, match="no válido"):
            TaxYear(2500)

    def test_non_int_rejected(self):
        with pytest.raises(ValueError, match="entero"):
            TaxYear(2026.5)


class TestTaxCategoryName:
    def test_valid_name(self):
        assert str(TaxCategoryName("  Salud  ")) == "Salud"

    def test_empty_rejected(self):
        with pytest.raises(ValueError, match="requerido"):
            TaxCategoryName("   ")

    def test_too_long_rejected(self):
        with pytest.raises(ValueError, match="200 caracteres"):
            TaxCategoryName("x" * 201)


class TestTaxDeductionDescription:
    def test_valid(self):
        assert str(TaxDeductionDescription("Prima de seguro médico")) == "Prima de seguro médico"

    def test_empty_rejected(self):
        with pytest.raises(ValueError, match="requerid"):
            TaxDeductionDescription("")


class TestMoneyAmount:
    def test_quantizes_to_two_decimals(self):
        assert MoneyAmount(Decimal("10.005")).value == Decimal("10.01")

    def test_negative_rejected(self):
        with pytest.raises(ValueError, match="negativo"):
            MoneyAmount(Decimal("-5"))

    def test_zero_allowed(self):
        assert MoneyAmount(Decimal("0")).value == Decimal("0")
