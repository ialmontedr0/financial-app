"""Storage factory: returns the configured backend."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.infrastructure.storage.file_storage import LocalStorageBackend


@lru_cache
def get_storage_backend():
    """Retorna el storage del backend configurado via STORAGE_DRIVER."""
    settings = get_settings()

    if settings.STORAGE_DRIVER == "s3":
        from app.infrastructure.storage.s3_storage import S3StorageBackend

        return S3StorageBackend(
            bucket=settings.S3_BUCKET,
            endpoint_url=settings.S3_ENDPOINT_URL or None,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            region=settings.S3_REGION,
        )

    return LocalStorageBackend()
