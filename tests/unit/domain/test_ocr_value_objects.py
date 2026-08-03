"""OCR domain value objects unit tests."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.domain.ocr.value_objects import ExtractedReceipt, validate_ocr_file


@pytest.mark.unit
class TestExtractedReceipt:
    def test_empty_receipt_is_not_complete(self) -> None:
        receipt = ExtractedReceipt(raw_text="")
        assert receipt.is_complete is False
        assert receipt.missing_fields == ["amount", "date", "merchant"]

    def test_complete_receipt(self) -> None:
        receipt = ExtractedReceipt(
            raw_text="TOTAL $50.00",
            amount=Decimal("50.00"),
            date=date(2026, 3, 15),
            merchant="Tienda XYZ",
            currency="USD",
            confidence="high",
        )
        assert receipt.is_complete is True
        assert receipt.missing_fields == []

    def test_partial_receipt_missing_fields(self) -> None:
        receipt = ExtractedReceipt(raw_text="x", amount=Decimal("10"))
        assert receipt.missing_fields == ["date", "merchant"]


@pytest.mark.unit
class TestValidateOcrFile:
    @pytest.mark.parametrize(
        ("filename", "content_type"),
        [
            ("recibo.png", "image/png"),
            ("recibo.JPG", "image/jpeg"),
            ("recibo.pdf", "application/pdf"),
            ("recibo.tiff", "image/tiff"),
        ],
    )
    def test_valid_files(self, filename: str, content_type: str) -> None:
        validate_ocr_file(filename, content_type)

    @pytest.mark.parametrize(
        ("filename", "content_type"),
        [
            ("recibo.txt", "text/plain"),
            ("recibo", "image/png"),
            ("recibo.png", "text/plain"),
            ("recibo.exe", "application/octet-stream"),
        ],
    )
    def test_invalid_files(self, filename: str, content_type: str) -> None:
        with pytest.raises(ValueError):
            validate_ocr_file(filename, content_type)
