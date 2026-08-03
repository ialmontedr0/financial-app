"""Cifrado de secretos de terceros (Plaid access tokens) con Fernet."""

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

import structlog
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings
from app.middleware.error_handler import ValidationError

logger = structlog.get_logger()


def _derive_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache
def _fernet() -> Fernet:
    settings = get_settings()
    if not settings.ENCRYPTION_KEY:
        raise ValidationError("ENCRYPTION_KEY no configurado; no se pueden almacenar tokens cifrados")
    return Fernet(_derive_key(settings.ENCRYPTION_KEY))


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:  # pragma: no cover
        logger.error("secret_decrypt_failed")
        raise ValidationError("No se pudo descifrar el token almacenado") from exc
