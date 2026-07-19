"""Tests for Wallet domain value objects."""

import pytest

from app.domain.wallet.value_objects import LiquidityLevel, WalletStatus, WalletType


class TestWalletType:
    def test_valid_types(self):
        for t in ["personal", "business", "savings", "investment", "daily", "emergency"]:
            assert str(WalletType(t)) == t

    def test_normalized_uppercase(self):
        assert str(WalletType("PERSONAL")) == "personal"
        assert str(WalletType("Emergency")) == "emergency"

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="Tipo de wallet no soportado"):
            WalletType("invalid_type")

    def test_name_property(self):
        assert WalletType("personal").name == "Personal"
        assert WalletType("emergency").name == "Fondo de Emergencia"


class TestWalletStatus:
    def test_valid_statuses(self):
        for s in ["active", "archived"]:
            assert str(WalletStatus(s)) == s

    def test_normalized(self):
        assert str(WalletStatus("ACTIVE")) == "active"

    def test_invalid_status(self):
        with pytest.raises(ValueError, match="Estado de wallet no soportado"):
            WalletStatus("deleted")

    def test_name_property(self):
        assert WalletStatus("active").name == "Activa"


class TestLiquidityLevel:
    def test_valid_levels(self):
        for level in ["high", "medium", "low", "mixed"]:
            assert str(LiquidityLevel(level)) == level

    def test_normalized(self):
        assert str(LiquidityLevel("HIGH")) == "high"

    def test_invalid_level(self):
        with pytest.raises(ValueError, match="Nivel de liquidez no soportado"):
            LiquidityLevel("very_high")

    def test_name_property(self):
        assert LiquidityLevel("high").name == "Alta - Acceso inmediato"
