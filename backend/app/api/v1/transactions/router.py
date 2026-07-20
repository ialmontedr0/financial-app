"""Transaction endpoints - 20 routes."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.api.deps import get_current_active_user, get_db

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/transactions", tags=["Transactions"])


# ======================================================================
# Transaction CRUD
# ======================================================================

@router.post("", status_code=201)
async def create_transaction(
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from datetime import date as date_type

    from app.application.transactions.create_transaction import CreateTransactionUseCase

    effective_date = date_type.fromisoformat(body["effective_date"]) if isinstance(body.get("effective_date"), str) else body.get("effective_date")
    tags = body.pop("tags", None)
    return await CreateTransactionUseCase(db).execute(
        user_id=uuid.UUID(current_user["sub"]), account_id=body["account_id"], transaction_type=body["transaction_type"],
        amount=body["amount"], currency_code=body.get("currency_code", "DOP"), description=body["description"],
        effective_date=effective_date, category_id=body.get("category_id"), subcategory_id=body.get("subcategory_id"),
        status=body.get("status", "completed"), notes=body.get("notes"), source=body.get("source", "manual"), tags=tags,
    )


@router.get("")
async def list_transactions(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    transaction_type: str | None = Query(None),
    status: str | None = Query(None),
    category_id: str | None = Query(None),
    subcategory_id: str | None = Query(None),
    account_id: str | None = Query(None),
    tag: str | None = Query(None),
    min_amount: float | None = Query(None),
    max_amount: float | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    source: str | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("effective_date"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    from datetime import date as date_type

    from app.application.transactions.list_transactions import ListTransactionsUseCase

    d_from = date_type.fromisoformat(date_from) if date_from else None
    d_to = date_type.fromisoformat(date_to) if date_to else None
    return await ListTransactionsUseCase(db).execute(
        uuid.UUID(current_user["sub"]), transaction_type=transaction_type, status=status, category_id=category_id,
        subcategory_id=subcategory_id, account_id=account_id, tag=tag, min_amount=min_amount, max_amount=max_amount,
        date_from=d_from, date_to=d_to, source=source, search=search, sort_by=sort_by, sort_order=sort_order,
        page=page, page_size=page_size,
    )


@router.get("/summary")
async def get_transaction_summary(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    date_from: str = Query(...),
    date_to: str = Query(...),
) -> dict:
    from datetime import date as date_type

    from app.application.transactions.get_transaction_summary import GetTransactionSummaryUseCase

    return await GetTransactionSummaryUseCase(db).execute(
        uuid.UUID(current_user["sub"]), date_type.fromisoformat(date_from), date_type.fromisoformat(date_to),
    )


# ======================================================================
# Transfer
# ======================================================================

@router.post("/transfer", status_code=201)
async def create_transfer(
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from datetime import date as date_type

    from app.application.transactions.create_transfer import CreateTransferUseCase

    effective_date = date_type.fromisoformat(body["effective_date"]) if isinstance(body.get("effective_date"), str) else body.get("effective_date")
    return await CreateTransferUseCase(db).execute(
        user_id=uuid.UUID(current_user["sub"]), source_account_id=body["source_account_id"],
        destination_account_id=body["destination_account_id"], amount=body["amount"],
        currency_code=body.get("currency_code", "DOP"), description=body["description"],
        effective_date=effective_date, notes=body.get("notes"), tags=body.get("tags"),
    )


# ======================================================================
# Recurring (MUST be before /{transaction_id} to avoid route shadowing)
# ======================================================================

@router.post("/recurring", status_code=201)
async def create_recurring(
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from datetime import date as date_type

    from app.application.transactions.create_recurring import CreateRecurringUseCase

    start_date = date_type.fromisoformat(body["start_date"]) if isinstance(body.get("start_date"), str) else body.get("start_date")
    end_date = date_type.fromisoformat(body["end_date"]) if isinstance(body.get("end_date"), str) else body.get("end_date")
    return await CreateRecurringUseCase(db).execute(
        user_id=uuid.UUID(current_user["sub"]), account_id=body["account_id"], transaction_type=body["transaction_type"],
        amount=body["amount"], currency_code=body.get("currency_code", "DOP"), description=body["description"],
        frequency=body["frequency"], start_date=start_date, interval=body.get("interval", 1),
        category_id=body.get("category_id"), subcategory_id=body.get("subcategory_id"),
        notes=body.get("notes"), end_date=end_date, max_executions=body.get("max_executions"),
    )


@router.get("/recurring")
async def list_recurring(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    is_active: bool | None = Query(None),
) -> dict:
    from app.application.transactions.list_recurring import ListRecurringUseCase
    return await ListRecurringUseCase(db).execute(uuid.UUID(current_user["sub"]), is_active=is_active)


@router.get("/recurring/{recurring_id}")
async def get_recurring(
    recurring_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.transactions.list_recurring import ListRecurringUseCase
    from app.middleware.error_handler import NotFoundError
    recs = await ListRecurringUseCase(db).execute(uuid.UUID(current_user["sub"]))
    for r in recs.get("recurring", []):
        if r["id"] == str(recurring_id):
            return r
    raise NotFoundError("Recurring Pattern")


@router.patch("/recurring/{recurring_id}")
async def update_recurring(
    recurring_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.transactions.update_recurring import UpdateRecurringUseCase
    return await UpdateRecurringUseCase(db).execute(uuid.UUID(current_user["sub"]), recurring_id, **body)


@router.delete("/recurring/{recurring_id}")
async def delete_recurring(
    recurring_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.transactions.delete_recurring import DeleteRecurringUseCase
    return await DeleteRecurringUseCase(db).execute(uuid.UUID(current_user["sub"]), recurring_id)


@router.post("/recurring/process", status_code=200)
async def process_recurring(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.transactions.process_recurring import ProcessRecurringUseCase
    return await ProcessRecurringUseCase(db).execute()


# ======================================================================
# OCR (Stub)
# ======================================================================

@router.post("/ocr")
async def ocr_receipt(
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return {"success": False, "message": "OCR no disponible aun. Estara disponible en Fase 20.", "data": None}


# ======================================================================
# Transaction by ID (MUST be AFTER /summary, /transfer, /recurring, /ocr)
# ======================================================================

@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.transactions.get_transaction import GetTransactionUseCase
    return await GetTransactionUseCase(db).execute(uuid.UUID(current_user["sub"]), transaction_id)


@router.patch("/{transaction_id}")
async def update_transaction(
    transaction_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from datetime import date as date_type

    from app.application.transactions.update_transaction import UpdateTransactionUseCase

    if "effective_date" in body and isinstance(body["effective_date"], str):
        body["effective_date"] = date_type.fromisoformat(body["effective_date"])
    return await UpdateTransactionUseCase(db).execute(uuid.UUID(current_user["sub"]), transaction_id, changes=body)


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.transactions.delete_transaction import DeleteTransactionUseCase
    return await DeleteTransactionUseCase(db).execute(uuid.UUID(current_user["sub"]), transaction_id)


@router.post("/{transaction_id}/tags", status_code=201)
async def add_tags(
    transaction_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.transactions.add_tags import AddTagsUseCase
    return await AddTagsUseCase(db).execute(uuid.UUID(current_user["sub"]), transaction_id, body["tags"])


@router.delete("/{transaction_id}/tags/{tag_name}")
async def remove_tag(
    transaction_id: uuid.UUID,
    tag_name: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.transactions.remove_tag import RemoveTagUseCase
    return await RemoveTagUseCase(db).execute(uuid.UUID(current_user["sub"]), transaction_id, tag_name)


@router.post("/{transaction_id}/attachments", status_code=201)
async def upload_attachment(
    transaction_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.transactions.upload_attachment import UploadAttachmentUseCase

    content = await file.read()
    return await UploadAttachmentUseCase(db).execute(
        uuid.UUID(current_user["sub"]), transaction_id, filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream", content=content,
    )


@router.get("/{transaction_id}/attachments")
async def list_attachments(
    transaction_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.transactions.list_attachments import ListAttachmentsUseCase
    return await ListAttachmentsUseCase(db).execute(uuid.UUID(current_user["sub"]), transaction_id)


@router.delete("/{transaction_id}/attachments/{attachment_id}")
async def delete_attachment(
    transaction_id: uuid.UUID,
    attachment_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.transactions.delete_attachment import DeleteAttachmentUseCase
    return await DeleteAttachmentUseCase(db).execute(uuid.UUID(current_user["sub"]), attachment_id)


@router.get("/{transaction_id}/audit")
async def get_audit_log(
    transaction_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.transactions.get_audit_log import GetAuditLogUseCase
    return await GetAuditLogUseCase(db).execute(uuid.UUID(current_user["sub"]), transaction_id)
