"""Use case: extraer datos de un recibo mediante OCR."""

from __future__ import annotations

from typing import Any

import structlog

from app.infrastructure.ocr.ocr_engine import OcrEngine
from app.middleware.error_handler import ValidationError

logger = structlog.get_logger()


class ExtractReceiptUseCase:
    def __init__(self, engine: OcrEngine | None = None) -> None:
        self._engine = engine or OcrEngine()

    def execute(self, filename: str, content_type: str, data: bytes) -> dict[str, Any]:
        try:
            receipt = self._engine.extract(filename, content_type, data)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        result: dict[str, Any] = {
            "success": receipt.amount is not None,
            "data": {
                "text": receipt.raw_text,
                "amount": float(receipt.amount) if receipt.amount is not None else None,
                "amount_decimal": str(receipt.amount) if receipt.amount is not None else None,
                "date": receipt.date.isoformat() if receipt.date is not None else None,
                "merchant": receipt.merchant,
                "currency": receipt.currency,
                "confidence": receipt.confidence,
            },
            "suggestions": {
                "amount": float(receipt.amount) if receipt.amount is not None else None,
                "date": receipt.date.isoformat() if receipt.date is not None else None,
                "merchant": receipt.merchant,
                "currency": receipt.currency,
                "type": "expense",
            },
            "warnings": list(receipt.warnings),
        }

        logger.info(
            "ocr_receipt_extracted",
            filename=filename,
            amount=float(receipt.amount) if receipt.amount is not None else None,
            confidence=receipt.confidence,
        )
        return result
