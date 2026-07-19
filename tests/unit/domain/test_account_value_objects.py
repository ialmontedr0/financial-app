"""Tests for Accounts domain value objects."""

from decimal import Decimal

import pytest

from app.domain.accounts.value_objects import AccountBalance, AccountStatus, AccountType


class TestAccountType:
    def test_valid_types(self):
        for t in ["bank", "cash", "savings", "checking", "wallet", "crypto"]:
            assert str(AccountType(t)) == t

    def test_normalized_uppercase(self):
        assert str(AccountType("BANK")) == "bank"
        assert str(AccountType("Crypto")) == "crypto"

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="Tipo de cuenta no soportado"):
            AccountType("invalid_type")

    def test_name_property(self):
        assert AccountType("bank").name == "Cuenta Bancaria"
        assert AccountType("crypto").name == "Criptomonedas"


class TestAccountStatus:
    def test_valid_statuses(self):
        for s in ["active", "inactive", "archived", "frozen"]:
            assert str(AccountStatus(s)) == s

    def test_normalized(self):
        assert str(AccountStatus("ACTIVE")) == "active"

    def test_invalid_status(self):
        with pytest.raises(ValueError, match="Estado de cuenta no soportado"):
            AccountStatus("deleted")

    def test_name_property(self):
        assert AccountStatus("active").name == "Activa"


class TestAccountBalance:
    def test_valid_balance(self):
        b = AccountBalance(amount=Decimal("1000.50"), currency="DOP")
        assert b.amount == Decimal("1000.50")
        assert b.currency == "DOP"

    def test_string_representation(self):
        b = AccountBalance(amount=Decimal("500"), currency="USD")
        assert str(b) == "500 USD"

    def test_add_same_currency(self):
        a = AccountBalance(amount=Decimal("100"), currency="USD")
        b = AccountBalance(amount=Decimal("50"), currency="USD")
        result = a + b
        assert result.amount == Decimal("150")

    def test_add_different_currency_raises(self):
        a = AccountBalance(amount=Decimal("100"), currency="USD")
        b = AccountBalance(amount=Decimal("50"), currency="EUR")
        with pytest.raises(ValueError, match="diferentes monedas"):
            a + b

    def test_sub_same_currency(self):
        a = AccountBalance(amount=Decimal("100"), currency="USD")
        b = AccountBalance(amount=Decimal("30"), currency="USD")
        result = a - b
        assert result.amount == Decimal("70")
