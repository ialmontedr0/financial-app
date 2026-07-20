"""Pydantic schemas for transaction endpoints."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

# === Transaction ===

class CreateTransactionRequest(BaseModel):
    account_id: str
    transaction_type: str = Field(..., description="income, expense, adjustment")
    amount: float = Field(..., gt=0)
    currency_code: str = Field(default="DOP", max_length=3)
    description: str = Field(..., min_length=1, max_length=500)
    effective_date: date
    category_id: str | None = None
    subcategory_id: str | None = None
    status: str = Field(default="completed")
    notes: str | None = None
    source: str = Field(default="manual")
    tags: list[str] | None = None


class TransactionResponse(BaseModel):
    id: str
    account_id: str
    category_id: str | None = None
    subcategory_id: str | None = None
    transaction_type: str
    status: str
    amount: str
    currency_code: str
    description: str
    notes: str | None = None
    effective_date: str | None = None
    transfer_id: str | None = None
    source: str
    tags: list[str] = []
    created_at: str | None = None


class AttachmentInfo(BaseModel):
    id: str
    original_filename: str
    mime_type: str
    file_size: int
    created_at: str | None = None


class TransactionDetailResponse(TransactionResponse):
    recurring_id: str | None = None
    ai_category_id: str | None = None
    ai_confidence: str | None = None
    ai_model_version: str | None = None
    ai_reason: str | None = None
    attachments: list[AttachmentInfo] = []
    updated_at: str | None = None


class UpdateTransactionRequest(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=500)
    notes: str | None = None
    category_id: str | None = None
    subcategory_id: str | None = None
    status: str | None = None
    effective_date: date | None = None
    account_id: str | None = None


class DeleteTransactionResponse(BaseModel):
    id: str
    status: str
    message: str


class TransactionListItem(BaseModel):
    id: str
    account_id: str
    category_id: str | None = None
    subcategory_id: str | None = None
    transaction_type: str
    status: str
    amount: str
    currency_code: str
    description: str
    effective_date: str | None = None
    source: str
    tags: list[str] = []
    created_at: str | None = None


class ListTransactionsResponse(BaseModel):
    transactions: list[TransactionListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# === Transfer ===

class TransferCreateRequest(BaseModel):
    source_account_id: str
    destination_account_id: str
    amount: float = Field(..., gt=0)
    currency_code: str = Field(default="DOP", max_length=3)
    description: str = Field(..., min_length=1, max_length=500)
    effective_date: date
    notes: str | None = None
    tags: list[str] | None = None


class TransferTransactionInfo(BaseModel):
    id: str
    account_id: str
    amount: str
    type: str


class TransferResponse(BaseModel):
    transfer_id: str
    source_transaction: TransferTransactionInfo
    destination_transaction: TransferTransactionInfo
    total_amount: str
    currency_code: str
    effective_date: str
    created_at: str | None = None


# === Summary ===

class TransactionSummaryResponse(BaseModel):
    period_start: str
    period_end: str
    total_income: str
    total_expenses: str
    net_flow: str
    total_income_count: int
    total_expense_count: int
    total_transfer_count: int
    total_adjustment_count: int
    by_type: dict[str, Any]


# === Tags ===

class AddTagsRequest(BaseModel):
    tags: list[str] = Field(..., min_length=1)


class TagResponse(BaseModel):
    transaction_id: str
    added: list[str] = []
    total_tags: int
    all_tags: list[str]


class RemoveTagResponse(BaseModel):
    transaction_id: str
    removed_tag: str
    remaining_tags: list[str]


# === Attachments ===

class UploadAttachmentResponse(BaseModel):
    id: str
    transaction_id: str
    original_filename: str
    mime_type: str
    file_size: int
    created_at: str | None = None


class ListAttachmentsResponse(BaseModel):
    transaction_id: str
    attachments: list[AttachmentInfo]
    total: int


class DeleteAttachmentResponse(BaseModel):
    id: str
    message: str


# === Recurring ===

class CreateRecurringRequest(BaseModel):
    account_id: str
    transaction_type: str
    amount: float = Field(..., gt=0)
    currency_code: str = Field(default="DOP", max_length=3)
    description: str = Field(..., min_length=1, max_length=500)
    frequency: str
    start_date: date
    interval: int = Field(default=1, ge=1)
    category_id: str | None = None
    subcategory_id: str | None = None
    notes: str | None = None
    end_date: date | None = None
    max_executions: int | None = None


class RecurringResponse(BaseModel):
    id: str
    transaction_type: str
    amount: str
    currency_code: str
    description: str
    frequency: str
    interval: int
    start_date: str
    end_date: str | None = None
    next_execution_date: str
    max_executions: int | None = None
    execution_count: int
    is_active: bool
    created_at: str | None = None


class RecurringListItem(BaseModel):
    id: str
    transaction_type: str
    amount: str
    currency_code: str
    description: str
    frequency: str
    interval: int
    start_date: str
    end_date: str | None = None
    next_execution_date: str
    execution_count: int
    max_executions: int | None = None
    is_active: bool
    last_executed_at: str | None = None


class ListRecurringResponse(BaseModel):
    recurring: list[RecurringListItem]
    total: int


class UpdateRecurringRequest(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=500)
    frequency: str | None = None
    interval: int | None = Field(default=None, ge=1)
    end_date: date | None = None
    max_executions: int | None = None
    is_active: bool | None = None


class DeleteRecurringResponse(BaseModel):
    id: str
    message: str


class ProcessRecurringResponse(BaseModel):
    processed: int
    created: int
    errors: list[dict]


# === OCR ===

class OCRRequest(BaseModel):
    image_url: str | None = None


class OCRResponse(BaseModel):
    success: bool
    message: str
    data: dict | None = None


# === Audit ===

class AuditLogEntry(BaseModel):
    id: str
    action: str
    changes: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: str | None = None


class AuditLogResponse(BaseModel):
    transaction_id: str
    audit_logs: list[AuditLogEntry]
    total: int
