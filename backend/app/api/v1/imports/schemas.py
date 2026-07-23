"""Schemas for import endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ImportPreviewResponse(BaseModel):
    job_id: UUID
    file_name: str
    file_type: str
    total_rows: int
    columns_found: list[str]
    preview_rows: list[dict[str, Any]]
    validation_errors: list[dict[str, Any]]
    duplicates_found: int


class ImportConfirmRequest(BaseModel):
    job_id: UUID


class ImportConfirmResponse(BaseModel):
    success: bool
    job_id: UUID
    total_rows: int
    valid_rows: int
    error_rows: int
    errors: list[dict[str, Any]] | None = None


class ImportJobResponse(BaseModel):
    id: UUID
    file_name: str
    file_type: str
    import_type: str
    status: str
    total_rows: int
    processed_rows: int
    valid_rows: int
    error_rows: int
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ImportJobListResponse(BaseModel):
    jobs: list[ImportJobResponse]
    total: int
