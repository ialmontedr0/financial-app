"""Unit tests for insurance value objects."""

from __future__ import annotations

import pytest

from app.domain.insurance.value_objects import (
    InsuranceStatus,
    InsuranceType,
    PaymentMethod,
    PremiumFrequency,
    PremiumStatus,
)


class TestInsuranceType:
    def test_valid_types(self):
        assert str(InsuranceType("health")) == "health"
        assert str(InsuranceType("AUTO")) == "auto"
        assert InsuranceType("life").name == "Seguro de Vida"

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="no soportado"):
            InsuranceType("pet")


class TestInsuranceStatus:
    def test_valid_statuses(self):
        assert str(InsuranceStatus("active")) == "active"
        assert str(InsuranceStatus("CANCELLED")) == "cancelled"
        assert InsuranceStatus("expired").name == "Expirado"

    def test_invalid_status(self):
        with pytest.raises(ValueError, match="no soportado"):
            InsuranceStatus("lost")


class TestPremiumFrequency:
    def test_payments_per_year(self):
        assert PremiumFrequency("monthly").payments_per_year == 12
        assert PremiumFrequency("quarterly").payments_per_year == 4
        assert PremiumFrequency("semi_annual").payments_per_year == 2
        assert PremiumFrequency("annual").payments_per_year == 1

    def test_invalid_frequency(self):
        with pytest.raises(ValueError, match="no soportado"):
            PremiumFrequency("weekly")


class TestPremiumStatus:
    def test_valid_statuses(self):
        assert str(PremiumStatus("paid")) == "paid"
        assert str(PremiumStatus("OVERDUE")) == "overdue"
        assert PremiumStatus("pending").name == "Pendiente"

    def test_invalid_status(self):
        with pytest.raises(ValueError, match="no soportado"):
            PremiumStatus("refunded")


class TestPaymentMethod:
    def test_valid_method(self):
        assert str(PaymentMethod("bank_transfer")) == "bank_transfer"
        assert PaymentMethod("cash").name == "Efectivo"

    def test_invalid_method(self):
        with pytest.raises(ValueError, match="no soportado"):
            PaymentMethod("crypto")
