"""Import API endpoints."""

from __future__ import annotations

import uuid

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.api.v1.imports import schemas as import_schemas
from app.infrastructure.models.import_job import ImportJobModel

router = APIRouter(prefix="/imports", tags=["Imports"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@router.post("/transactions", response_model=import_schemas.ImportPreviewResponse)
async def upload_transactions(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload CSV/Excel file of transactions for import."""
    file_ext = ""
    if file.filename:
        file_ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Use: {ALLOWED_EXTENSIONS}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    try:
        if file_ext == ".csv":
            from app.integrations.csv_handler import parse_csv, validate_rows

            df = parse_csv(content)
            file_type = "csv"
        else:
            from app.integrations.excel_handler import parse_excel
            from app.integrations.excel_handler import validate_rows_xlsx as validate_rows

            df = parse_excel(content)
            file_type = "xlsx"
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing file: {e!s}") from e

    errors = validate_rows(df)

    job = ImportJobModel(
        user_id=uuid.UUID(current_user["sub"]),
        file_name=file.filename or "unknown",
        file_type=file_type,
        import_type="transactions",
        status="pending",
        total_rows=len(df),
        preview_data=df.head(10).to_dict(orient="records"),
        mapping_config={"columns": list(df.columns)},
    )
    db.add(job)
    await db.flush()

    return import_schemas.ImportPreviewResponse(
        job_id=job.id,
        file_name=job.file_name,
        file_type=job.file_type,
        total_rows=len(df),
        columns_found=list(df.columns),
        preview_rows=df.head(10).to_dict(orient="records"),
        validation_errors=errors,
        duplicates_found=0,
    )


@router.post("/confirm", response_model=import_schemas.ImportConfirmResponse)
async def confirm_import(
    body: import_schemas.ImportConfirmRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm and execute a pending import job."""
    user_id = uuid.UUID(current_user["sub"])

    result = await db.execute(
        select(ImportJobModel).where(
            ImportJobModel.id == body.job_id,
            ImportJobModel.user_id == user_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    if job.status != "pending":
        raise HTTPException(status_code=400, detail=f"Job is already {job.status}")

    if not job.preview_data:
        raise HTTPException(status_code=400, detail="No data to import")

    from app.integrations.import_processor import process_import

    preview_df = pd.DataFrame(job.preview_data)
    if job.file_type == "csv":
        from app.integrations.csv_handler import df_to_transactions

        transactions = df_to_transactions(preview_df)
    else:
        from app.integrations.excel_handler import df_to_transactions_xlsx as df_to_transactions

        transactions = df_to_transactions(preview_df)

    proc_result = await process_import(db, user_id, transactions, job)

    return import_schemas.ImportConfirmResponse(
        success=True,
        job_id=job.id,
        total_rows=proc_result["total"],
        valid_rows=proc_result["valid"],
        error_rows=proc_result["errors"],
        errors=proc_result.get("error_details"),
    )


@router.get("/jobs", response_model=import_schemas.ImportJobListResponse)
async def list_import_jobs(
    skip: int = 0,
    limit: int = 20,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List import jobs for the current user."""
    user_id = uuid.UUID(current_user["sub"])
    result = await db.execute(
        select(ImportJobModel)
        .where(ImportJobModel.user_id == user_id)
        .order_by(ImportJobModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    jobs = result.scalars().all()
    return import_schemas.ImportJobListResponse(jobs=jobs, total=len(jobs))


@router.get("/jobs/{job_id}", response_model=import_schemas.ImportJobResponse)
async def get_import_job(
    job_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific import job."""
    result = await db.execute(
        select(ImportJobModel).where(
            ImportJobModel.id == job_id,
            ImportJobModel.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")
    return job
