"""Local filesystem storage for transaction attachments."""

from __future__ import annotations

import uuid
from pathlib import Path

import structlog

logger = structlog.get_logger()

UPLOAD_ROOT = Path("backend/uploads")


class LocalStorageBackend:
    """Almacenamiento en el sistema de archivos local."""

    def store_file(
        self,
        user_id: uuid.UUID,
        transaction_id: uuid.UUID,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> dict:
        ext = Path(filename).suffix.lower()
        stored_name = f"{uuid.uuid4()}{ext}"
        directory = UPLOAD_ROOT / str(user_id) / str(transaction_id)
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / stored_name
        file_path.write_bytes(content)
        storage_path = str(file_path.relative_to(UPLOAD_ROOT))
        logger.info(
            "file_stored",
            user_id=str(user_id),
            tx_id=str(transaction_id),
            original=filename,
            size=len(content),
        )
        return {
            "filename": stored_name,
            "original_filename": filename,
            "mime_type": content_type,
            "file_size": len(content),
            "storage_path": storage_path,
        }

    def delete_file(self, storage_path: str) -> bool:
        full_path = UPLOAD_ROOT / storage_path
        if full_path.exists():
            full_path.unlink()
            logger.info("file_deleted", path=storage_path)
            return True
        return False

    def get_url(self, storage_path: str, *, expires_in: int = 900) -> str | None:  # noqa: ARG002
        return None


# --- Legacy module-level helpers (keep for backwards compatibility) ----------
_local = LocalStorageBackend()


def get_upload_directory(user_id: uuid.UUID, transaction_id: uuid.UUID) -> Path:
    path = UPLOAD_ROOT / str(user_id) / str(transaction_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def store_file(
    user_id: uuid.UUID, transaction_id: uuid.UUID, filename: str, content: bytes, content_type: str
) -> dict:
    return _local.store_file(user_id, transaction_id, filename, content, content_type)


def delete_file(storage_path: str) -> bool:
    return _local.delete_file(storage_path)
