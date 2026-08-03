"""OCR endpoints: escaneo de recibos."""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_current_active_user
from app.application.ocr.extract_receipt import ExtractReceiptUseCase
from app.core.config import get_settings

logger = structlog.get_logger()

router = APIRouter(prefix="/ocr", tags=["OCR"])

settings = get_settings()


@router.post("/extract")
async def extract_receipt(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user),
):
    uuid.UUID(current_user["sub"])
    data = await file.read()
    return ExtractReceiptUseCase().execute(file.filename or "", file.content_type or "", data)


@router.get("/status")
async def ocr_status(
    current_user: dict = Depends(get_current_active_user),
):
    uuid.UUID(current_user["sub"])
    tesseract_available = False
    if settings.OCR_ENABLED:
        try:
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
            tesseract_available = bool(pytesseract.get_tesseract_version())
        except Exception:
            tesseract_available = False

    from app.domain.ocr.value_objects import SUPPORTED_EXTENSIONS

    return {
        "enabled": settings.OCR_ENABLED,
        "tesseract_available": tesseract_available,
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
    }
