"""Local filesystem storage for transaction attachments."""

from __future__ import annotations

import uuid
from pathlib import Path

import structlog

logger = structlog.get_logger()

UPLOAD_ROOT = Path("backend/uploads")


def get_upload_directory(user_id: uuid.UUID, transaction_id: uuid.UUID) -> Path:
    path = UPLOAD_ROOT / str(user_id) / str(transaction_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def store_file(user_id: uuid.UUID, transaction_id: uuid.UUID, filename: str, content: bytes, content_type: str) -> dict:
    ext = Path(filename).suffix.lower()
    stored_name = f"{uuid.uuid4()}{ext}"
    directory = get_upload_directory(user_id, transaction_id)
    file_path = directory / stored_name
    file_path.write_bytes(content)
    storage_path = str(file_path.relative_to(UPLOAD_ROOT))
    logger.info("file_stored", user_id=str(user_id), tx_id=str(transaction_id), original=filename, size=len(content))
    return {"filename": stored_name, "original_filename": filename, "mime_type": content_type, "file_size": len(content), "storage_path": storage_path}


def delete_file(storage_path: str) -> bool:
    full_path = UPLOAD_ROOT / storage_path
    if full_path.exists():
        full_path.unlink()
        logger.info("file_deleted", path=storage_path)
        return True
    return False
