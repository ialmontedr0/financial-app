"""Shared Pydantic validators."""

from __future__ import annotations

import re
import unicodedata

# Set de monedas ISO 4217 soportadas comunmente
VALID_CURRENCIES = {
    "MXN",
    "USD",
    "DOP",
    "EUR",
    "CAD",
    "GBP",
    "JPY",
    "CNY",
    "BRL",
    "ARS",
    "CLP",
    "COP",
    "PEN",
}

PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIREMENTS = {
    "uppercase": lambda p: any(c.isupper() for c in p),
    "lowercase": lambda p: any(c.islower() for c in p),
    "digit": lambda p: any(c.isdigit() for c in p),
    "special": lambda p: any(c in "!@#$%^&*()-_=+[]{};:,.<>?/|~`" for c in p),
}


def normalize_name(value: str) -> str:
    """Normaliza un nombre: limpia espacions y capitaliza palabras."""
    value = unicodedata.normalize("NFC", value.strip())
    value = re.sub(r"\s+", " ", value)
    return value.title()


def validate_currency(value: str) -> str:
    value = value.upper().strip()
    if value not in VALID_CURRENCIES:
        raise ValueError(f"Moneda no soportada: {value}")
    return value


def validate_password_strength(value: str) -> str:
    if len(value) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"La contrasena debe tener al menos {PASSWORD_MIN_LENGTH} caracteres.")
    missing = [name for name, check in PASSWORD_REQUIREMENTS.items() if not check(value)]
    if missing:
        raise ValueError(f"La contrasena debe incluir: {', '.join(missing)}")
    return value
