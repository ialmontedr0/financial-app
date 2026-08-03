"""Unit tests for multi-currency domain value objects."""

from decimal import Decimal

import pytest

from app.domain.currency.value_objects import CurrencyPair, Money, round_money
from app.domain.users.value_objects import SUPPORTED_CURRENCIES, CurrencyCode


@pytest.mark.unit
class TestCurrencyCode:
    def test_valid_code_is_normalized(self):
        assert CurrencyCode("dop").code == "DOP"

    def test_invalid_code_raises(self):
        with pytest.raises(ValueError):
            CurrencyCode("XXX")

    def test_supported_currencies_include_major_codes(self):
        assert {"DOP", "USD", "EUR", "MXN", "VES"} <= set(SUPPORTED_CURRENCIES)


@pytest.mark.unit
class TestCurrencyPair:
    def test_creates_validated_pair(self):
        pair = CurrencyPair("usd", "dop")
        assert pair.source == "USD"
        assert pair.target == "DOP"

    def test_invalid_currency_raises(self):
        with pytest.raises(ValueError):
            CurrencyPair("USD", "NOT")

    def test_same_currency_detection(self):
        assert CurrencyPair("USD", "USD").is_same_currency
        assert not CurrencyPair("USD", "EUR").is_same_currency

    def test_inverse_swaps_currencies(self):
        pair = CurrencyPair("USD", "EUR")
        assert pair.inverse.source == "EUR"
        assert pair.inverse.target == "USD"


@pytest.mark.unit
class TestMoney:
    def test_init_coerces_and_normalizes(self):
        money = Money(amount="10.5", currency="usd")
        assert money.amount == Decimal("10.5")
        assert money.currency == "USD"

    def test_init_rejects_invalid_currency(self):
        with pytest.raises(ValueError):
            Money(amount=Decimal("1"), currency="ZZZ")

    def test_add_same_currency(self):
        total = Money(Decimal("1.005"), "USD") + Money(Decimal("2.004"), "USD")
        assert total.amount == Decimal("3.009")

    def test_add_different_currency_raises(self):
        with pytest.raises(ValueError):
            Money(Decimal("1"), "USD") + Money(Decimal("1"), "EUR")

    def test_sub_same_currency(self):
        diff = Money(Decimal("5"), "USD") - Money(Decimal("1.5"), "USD")
        assert diff.amount == Decimal("3.5")

    def test_convert_same_currency_is_identity(self):
        money = Money(Decimal("42.1234"), "USD")
        assert money.convert(Decimal("2"), "USD") == money

    def test_convert_applies_rate_and_rounds(self):
        money = Money(Decimal("10"), "USD").convert(Decimal("56.5"), "DOP")
        assert money.amount == Decimal("565.0000")
        assert money.currency == "DOP"

    def test_convert_rounds_half_up(self):
        money = Money(Decimal("1.00005"), "USD").convert(Decimal("3"), "EUR")
        assert money.amount == Decimal("3.0002")

    def test_convert_rejects_non_positive_rate(self):
        money = Money(Decimal("10"), "USD")
        with pytest.raises(ValueError):
            money.convert(Decimal("0"), "EUR")
        with pytest.raises(ValueError):
            money.convert(Decimal("-1"), "EUR")

    def test_str_representation(self):
        assert str(Money(Decimal("1"), "USD")) == "1 USD"


@pytest.mark.unit
class TestRoundMoney:
    def test_rounds_to_four_decimals_half_up(self):
        assert round_money(Decimal("1.00005")) == Decimal("1.0001")
        assert round_money(Decimal("1.00004")) == Decimal("1.0000")
