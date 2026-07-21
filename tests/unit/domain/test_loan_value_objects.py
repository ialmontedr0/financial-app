"""Unit tests for loan value objects and calculations."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.application.loans.create_loan import (
    calculate_monthly_payment,
    generate_amortization_schedule,
)
from app.domain.loan.value_objects import (
    InterestType,
    LoanPaymentStatus,
    LoanStatus,
    LoanType,
    PaymentFrequency,
    PaymentMethod,
)


class TestLoanType:
    def test_valid_types(self):
        assert str(LoanType("personal")) == "personal"
        assert str(LoanType("MORTGAGE")) == "mortgage"
        assert LoanType("auto").name == "Auto"

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="no soportado"):
            LoanType("invalid")

    def test_case_insensitive(self):
        assert str(LoanType("PERSONAL")) == "personal"


class TestLoanStatus:
    def test_valid_statuses(self):
        assert str(LoanStatus("active")) == "active"
        assert str(LoanStatus("PAID_OFF")) == "paid_off"
        assert LoanStatus("defaulted").name == "En Incumplimiento"

    def test_invalid_status(self):
        with pytest.raises(ValueError, match="no soportado"):
            LoanStatus("unknown")


class TestPaymentFrequency:
    def test_monthly(self):
        freq = PaymentFrequency("monthly")
        assert freq.payments_per_year == 12

    def test_bi_weekly(self):
        freq = PaymentFrequency("bi_weekly")
        assert freq.payments_per_year == 26

    def test_weekly(self):
        freq = PaymentFrequency("weekly")
        assert freq.payments_per_year == 52


class TestInterestType:
    def test_fixed(self):
        assert InterestType("fixed").name == "Fijo"

    def test_variable(self):
        assert str(InterestType("variable")) == "variable"


class TestPaymentMethod:
    def test_valid_methods(self):
        assert PaymentMethod("bank_transfer").name == "Transferencia Bancaria"
        assert str(PaymentMethod("cash")) == "cash"

    def test_invalid_method(self):
        with pytest.raises(ValueError, match="no soportado"):
            PaymentMethod("bitcoin")


class TestLoanPaymentStatus:
    def test_valid(self):
        assert LoanPaymentStatus("completed").name == "Completado"

    def test_invalid(self):
        with pytest.raises(ValueError, match="no soportado"):
            LoanPaymentStatus("unknown")


class TestMonthlyPaymentCalculation:
    def test_standard_loan(self):
        """100k, 12% annual, 120 months."""
        pmt = calculate_monthly_payment(Decimal("100000"), Decimal("12"), 120)
        assert pmt == Decimal("1434.71")

    def test_zero_interest(self):
        """100k, 0%, 10 months -> 10k/month."""
        pmt = calculate_monthly_payment(Decimal("100000"), Decimal("0"), 10)
        assert pmt == Decimal("10000.00")

    def test_short_term(self):
        """10k, 24% annual, 6 months."""
        pmt = calculate_monthly_payment(Decimal("10000"), Decimal("24"), 6)
        assert pmt > 0

    def test_long_term(self):
        """500k, 8% annual, 360 months (30 years)."""
        pmt = calculate_monthly_payment(Decimal("500000"), Decimal("8"), 360)
        assert pmt > 0
        assert pmt < Decimal("500000")  # less than the full principal
        assert pmt == Decimal("3668.82")


class TestAmortizationSchedule:
    def test_schedule_length(self):
        schedule = generate_amortization_schedule(
            principal=Decimal("12000"),
            annual_rate=Decimal("18"),
            term_months=12,
            monthly_payment=Decimal("1108.81"),
            start_date=__import__("datetime").date(2026, 1, 1),
        )
        assert len(schedule) == 12

    def test_last_entry_balance_zero(self):
        schedule = generate_amortization_schedule(
            principal=Decimal("12000"),
            annual_rate=Decimal("18"),
            term_months=12,
            monthly_payment=Decimal("1108.81"),
            start_date=__import__("datetime").date(2026, 1, 1),
        )
        assert schedule[-1]["balance_after"] == Decimal("0")

    def test_principal_sums_to_original(self):
        schedule = generate_amortization_schedule(
            principal=Decimal("12000"),
            annual_rate=Decimal("18"),
            term_months=12,
            monthly_payment=Decimal("1108.81"),
            start_date=__import__("datetime").date(2026, 1, 1),
        )
        total_principal = sum(e["principal_portion"] for e in schedule)
        assert total_principal == Decimal("12000")

    def test_interest_decreases(self):
        schedule = generate_amortization_schedule(
            principal=Decimal("12000"),
            annual_rate=Decimal("18"),
            term_months=12,
            monthly_payment=Decimal("1108.81"),
            start_date=__import__("datetime").date(2026, 1, 1),
        )
        interests = [e["interest_portion"] for e in schedule]
        assert interests == sorted(interests, reverse=True)
