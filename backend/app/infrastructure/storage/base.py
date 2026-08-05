"""Storage backend interface."""

from __future__ import annotations

import uuid
from typing import Protocol


class StorageBackend(Protocol):
    """Contrato común para drivers de almacenamiento (local o S3/MinIO)."""

    def store_file(
        self,
        user_id: uuid.UUID,
        transaction_id: uuid.UUID,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> dict:
        """Store a file and return metadata (incl. storage_path)."""
        ...

    def delete_file(self, storage_path: str) -> bool:
        """Delete a file by its storage_path."""
        ...

    def get_url(self, storage_path: str, *, expires_in: int = 900) -> str | None:
        """Return a time-limited URL to read the file (None for local)."""
        ...
