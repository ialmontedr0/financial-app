"""Tests for Users domain value objects."""

import pytest

from app.domain.users.value_objects import (
    CountryCode,
    CurrencyCode,
    LanguageCode,
    TimezoneCode,
)


class TestCurrencyCode:
    def test_valid_currency(self):
        assert str(CurrencyCode("DOP")) == "DOP"
        assert str(CurrencyCode("usd")) == "USD"  # Normalized to uppercase

    def test_invalid_currency(self):
        with pytest.raises(ValueError, match="Moneda no soportada"):
            CurrencyCode("XYZ")

    def test_name_property(self):
        assert CurrencyCode("DOP").name == "Peso Dominicano"


class TestTimezoneCode:
    def test_valid_timezone(self):
        assert str(TimezoneCode("America/Santo_Domingo")) == "America/Santo_Domingo"

    def test_invalid_timezone(self):
        with pytest.raises(ValueError, match="Zona horaria no soportada"):
            TimezoneCode("Invalid/Zone")


class TestLanguageCode:
    def test_valid_language(self):
        assert str(LanguageCode("es")) == "es"
        assert str(LanguageCode("ES")) == "es"  # Normalized to lowercase

    def test_language_with_region(self):
        assert str(LanguageCode("es-DO")) == "es-do"

    def test_invalid_language(self):
        with pytest.raises(ValueError, match="Idioma no soportado"):
            LanguageCode("xy")


class TestCountryCode:
    def test_valid_country(self):
        assert str(CountryCode("DO")) == "DO"
        assert str(CountryCode("us")) == "US"  # Normalized to uppercase

    def test_invalid_country(self):
        with pytest.raises(ValueError, match="Codigo de ciudad ISO 3166-1 alpha-2 invalido"):
            CountryCode("ZZ")
