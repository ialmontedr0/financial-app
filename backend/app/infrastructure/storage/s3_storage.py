"""S3 / MinIO storage backend (boto3)."""

from __future__ import annotations

import uuid
from pathlib import Path

import structlog

logger = structlog.get_logger()


class S3StorageBackend:
    """Almacenamiento S3-compatible (AWS S3 o MinIO) usando boto3.

    Genera URLs prefirmadas para lectura; compatible con MinIO vía
    ``endpoint_url``.
    """

    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None = None,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
    ) -> None:
        import boto3
        from botocore.config import Config

        self._bucket = bucket
        self._endpoint_url = endpoint_url
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        self._client = session.client(
            "s3",
            endpoint_url=endpoint_url,
            config=Config(signature_version="s3v4"),
        )

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
        storage_path = f"{user_id}/{transaction_id}/{stored_name}"
        self._client.put_object(
            Bucket=self._bucket,
            Key=storage_path,
            Body=content,
            ContentType=content_type,
        )
        logger.info(
            "file_stored_s3",
            user_id=str(user_id),
            tx_id=str(transaction_id),
            key=storage_path,
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
        try:
            self._client.delete_object(Bucket=self._bucket, Key=storage_path)
            logger.info("file_deleted_s3", key=storage_path)
            return True
        except Exception as e:
            logger.warning("file_delete_s3_failed", key=storage_path, error=str(e))
            return False

    def get_url(self, storage_path: str, *, expires_in: int = 900) -> str | None:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": storage_path},
            ExpiresIn=expires_in,
        )
