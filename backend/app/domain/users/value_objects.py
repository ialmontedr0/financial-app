from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

# ==============================================================================
# Concurrencias Soportadas (ISO 4217)
# ==============================================================================
SUPPORTED_CURRENCIES: dict[str, str] = {
    "DOP": "Peso Dominicano",
    "USD": "Dolar Estadounidense",
    "EUR": "Euro",
    "GBP": "British Pound Sterling",
    "CAD": "Canadian Dollar",
    "MXN": "Mexican Peso",
    "COP": "Colombian Peso",
    "VES": "Venezuelan Bolivar",
    "ARS": "Argentine Peso",
    "CLP": "Chilean Peso",
    "PEN": "Peruvian Sol",
    "BRL": "Brazilian Real",
    "JPY": "Japanese Yen",
    "CHF": "Swiss Franc",
    "CNY": "Chinese Yuan",
    "INR": "Indian Rupee",
    "KRW": "South Korean Won",
    "AUD": "Australian Dollar",
    "NZD": "New Zealand Dollar",
}


# ==============================================================================
# Zonas Horarias soportadas (IANA)
# ==============================================================================
SUPPORTED_TIMEZONES: dict[str, str] = {
    "America/Santo_Domingo": "Atlantic Standard Time (AST)",
    "America/New_York": "Eastern Time (ET)",
    "America/Chicago": "Central Time (CT)",
    "America/Denver": "Mountain Time (MT)",
    "America/Los_Angeles": "Pacific Time (PT)",
    "America/Caribbean": "Caribbean Time",
    "America/Bogota": "Colombia Time (COT)",
    "America/Mexico_City": "Mexico Central Time (CST)",
    "America/Buenos_Aires": "Argentina Time (ART)",
    "America/Santiago": "Chile Standard Time (CLT)",
    "America/Lima": "Peru Time (PET)",
    "America/Sao_Paulo": "Brazil Time (BRT)",
    "Europe/London": "Greenwich Mean Time (GMT)",
    "Europe/Paris": "Central European Time (CET)",
    "Europe/Berlin": "Central European Time (CET)",
    "Europe/Madrid": "Central European Time (CET)",
    "Asia/Tokyo": "Japan Standard Time (JST)",
    "Asia/Shanghai": "China Standard Time (CST)",
    "Asia/Kolkata": "India Standard Time (IST)",
    "Australia/Sydney": "Australian Eastern Time (AET)",
    "UTC": "Coordinated Universal Time",
}


# ==============================================================================
# Idiomas soportados
# ==============================================================================
SUPPORTED_LANGUAGES: dict[str, str] = {
    "es": "Espanol",
    "en": "English",
    "pt": "Portugues",
    "fr": "Francais",
    "de": "Deutsch",
    "it": "Italiano",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
}


@dataclass(frozen=True)
class CurrencyCode:
    """Value object del codigo de modeda validado ISO 4217"""

    code: str

    def __post_init__(self) -> None:
        normalized = self.code.upper().strip()
        if normalized not in SUPPORTED_CURRENCIES:
            supported = ", ".join(sorted(SUPPORTED_CURRENCIES.keys()))
            raise ValueError(f"Moneda no soportada: {self.code}.Soportada: {supported}")
        # Reasignar valor normalizado
        object.__setattr__(self, "code", normalized)

    def __str__(self) -> str:
        return self.code

    @property
    def name(self) -> str:
        """Nombre de moneda legible por humano."""
        return SUPPORTED_CURRENCIES.get(self.code, self.code)


@dataclass(frozen=True)
class TimezoneCode:
    """Valor de objecto de la zonahoraria validada IANA."""

    timezone: str

    def __post_init__(self) -> None:
        if self.timezone not in SUPPORTED_TIMEZONES:
            supported = ", ".join(sorted(SUPPORTED_TIMEZONES.keys()))
            raise ValueError(f"Zona horaria no soportada: {self.timezone}. Soportada: {supported}")

    def __str__(self) -> str:
        return self.timezone

    @property
    def name(self) -> str:
        """Nombre de la zona horaria legible por humano."""
        return SUPPORTED_TIMEZONES.get(self.timezone, self.timezone)


@dataclass(frozen=True)
class LanguageCode:
    """Valor de objeto del lenguage validado ISO 639-1"""

    code: str

    def __post_init__(self) -> None:
        normalized = self.code.lower().strip()
        # Permitir estilo de etiquetas "es-DO" validar la base
        base = normalized.split("-")[0]
        if base not in SUPPORTED_LANGUAGES:
            supported = ", ".join(sorted(SUPPORTED_LANGUAGES.keys()))
            raise ValueError(f"Idioma no soportado: {self.code}.Soportado: {supported}")
        object.__setattr__(self, "code", normalized)

    def __str__(self) -> str:
        return self.code

    @property
    def name(self) -> str:
        """Nombre del idioma legible por humanos."""
        base = self.code.split("-")[0]
        return SUPPORTED_LANGUAGES.get(base, self.code)


@dataclass(frozen=True)
class CountryCode:
    """Valor de objeto del codigo de ciudad alpha-2 ISO 3166-1"""

    code: str

    _ISO_COUNTRIES: ClassVar[frozenset[str]] = frozenset(
        {
            "AD",
            "AE",
            "AF",
            "AG",
            "AL",
            "AM",
            "AO",
            "AR",
            "AT",
            "AU",
            "AZ",
            "BA",
            "BB",
            "BD",
            "BE",
            "BF",
            "BG",
            "BH",
            "BI",
            "BJ",
            "BN",
            "BO",
            "BR",
            "BS",
            "BT",
            "BW",
            "BY",
            "BZ",
            "CA",
            "CD",
            "CF",
            "CG",
            "CH",
            "CI",
            "CL",
            "CM",
            "CN",
            "CO",
            "CR",
            "CU",
            "CY",
            "CZ",
            "DE",
            "DJ",
            "DK",
            "DM",
            "DO",
            "DZ",
            "EC",
            "EE",
            "EG",
            "ES",
            "ET",
            "FI",
            "FJ",
            "FM",
            "FR",
            "GA",
            "GB",
            "GD",
            "GE",
            "GH",
            "GM",
            "GN",
            "GQ",
            "GR",
            "GT",
            "GW",
            "GY",
            "HN",
            "HR",
            "HT",
            "HU",
            "ID",
            "IE",
            "IL",
            "IN",
            "IQ",
            "IR",
            "IS",
            "IT",
            "JM",
            "JO",
            "JP",
            "KE",
            "KG",
            "KH",
            "KI",
            "KM",
            "KN",
            "KP",
            "KR",
            "KW",
            "KZ",
            "LA",
            "LB",
            "LC",
            "LI",
            "LK",
            "LR",
            "LS",
            "LT",
            "LU",
            "LV",
            "LY",
            "MA",
            "MC",
            "MD",
            "ME",
            "MG",
            "MK",
            "ML",
            "MM",
            "MN",
            "MR",
            "MT",
            "MU",
            "MV",
            "MW",
            "MX",
            "MY",
            "MZ",
            "NA",
            "NE",
            "NG",
            "NI",
            "NL",
            "NO",
            "NP",
            "NR",
            "NZ",
            "OM",
            "PA",
            "PE",
            "PG",
            "PH",
            "PK",
            "PL",
            "PS",
            "PT",
            "PW",
            "QA",
            "RO",
            "RS",
            "RU",
            "RW",
            "SA",
            "SB",
            "SC",
            "SD",
            "SE",
            "SG",
            "SI",
            "SK",
            "SL",
            "SM",
            "SN",
            "SO",
            "SR",
            "SS",
            "SV",
            "SY",
            "SZ",
            "TD",
            "TG",
            "TH",
            "TJ",
            "TL",
            "TM",
            "TN",
            "TO",
            "TR",
            "TT",
            "TV",
            "TW",
            "TZ",
            "UA",
            "UG",
            "US",
            "UY",
            "UZ",
            "VA",
            "VC",
            "VE",
            "VN",
            "VU",
            "WS",
            "YE",
            "ZA",
            "ZM",
            "ZW",
        }
    )

    def __post_init__(self) -> None:
        normalized = self.code.upper().strip()
        if normalized not in self._ISO_COUNTRIES:
            raise ValueError(f"Codigo de ciudad ISO 3166-1 alpha-2 invalido: {self.code}")
        object.__setattr__(self, "code", normalized)

    def __str__(self) -> str:
        return self.code
