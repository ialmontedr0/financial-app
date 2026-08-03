"""OCR engine unit tests (no require binarios Tesseract/Poppler)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from reportlab.pdfgen import canvas

from app.core.config import Settings
from app.infrastructure.ocr.ocr_engine import OcrEngine
from app.middleware.error_handler import ValidationError


def _settings(**overrides: object) -> Settings:
    return Settings(OCR_ENABLED=False, **overrides)


def _make_pdf(text_lines: list[str]) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    y = 720
    for line in text_lines:
        pdf.drawString(72, y, line)
        y -= 20
    pdf.save()
    return buffer.getvalue()


@pytest.mark.unit
class TestParsing:
    def test_to_decimal_us_format(self) -> None:
        engine = OcrEngine(_settings())
        assert engine._to_decimal("1,234.56") == Decimal("1234.56")
        assert engine._to_decimal("50.00") == Decimal("50.00")
        assert engine._to_decimal("1.234,56") == Decimal("1234.56")
        assert engine._to_decimal("1234,56") == Decimal("1234.56")
        assert engine._to_decimal("abc") is None

    def test_parse_amount_with_total_keyword(self) -> None:
        engine = OcrEngine(_settings())
        amount, currency = engine._parse_amount("Total: $1,234.56\nIVA incluido")
        assert amount == Decimal("1234.56")
        assert currency == "USD"

    def test_parse_amount_spanish_keyword(self) -> None:
        engine = OcrEngine(_settings())
        amount, _ = engine._parse_amount("IMPORTE 45.90\nGracias por su compra")
        assert amount == Decimal("45.90")

    def test_parse_amount_currency_candidate(self) -> None:
        engine = OcrEngine(_settings())
        amount, currency = engine._parse_amount("S/ 120.50\nPago con tarjeta")
        assert amount == Decimal("120.50")
        assert currency == "PEN"

    def test_parse_amount_none_when_missing(self) -> None:
        engine = OcrEngine(_settings())
        amount, currency = engine._parse_amount("Sin datos financieros aqui")
        assert amount is None
        assert currency is None

    def test_parse_date_ddmmyyyy(self) -> None:
        engine = OcrEngine(_settings())
        assert engine._parse_date("Fecha: 15/03/2026") == date(2026, 3, 15)

    def test_parse_date_iso(self) -> None:
        engine = OcrEngine(_settings())
        assert engine._parse_date("2026-07-01 comprobante") == date(2026, 7, 1)

    def test_parse_date_month_name(self) -> None:
        engine = OcrEngine(_settings())
        assert engine._parse_date("Emitido el 5 de marzo de 2026") == date(2026, 3, 5)

    def test_parse_date_none(self) -> None:
        engine = OcrEngine(_settings())
        assert engine._parse_date("no hay fecha") is None

    def test_parse_merchant_by_keyword(self) -> None:
        engine = OcrEngine(_settings())
        merchant = engine._parse_merchant("Establecimiento: Tienda El Sol\nTotal: $10.00")
        assert merchant == "Tienda El Sol"

    def test_parse_merchant_first_line_fallback(self) -> None:
        engine = OcrEngine(_settings())
        merchant = engine._parse_merchant("Supermercado Verde\nTotal: $10.00")
        assert merchant == "Supermercado Verde"

    def test_parse_merchant_skips_amount_lines(self) -> None:
        engine = OcrEngine(_settings())
        merchant = engine._parse_merchant("Total: $10.00\nSin establecimiento")
        assert merchant is not None


@pytest.mark.unit
class TestExtract:
    def test_extract_pdf_with_text(self) -> None:
        engine = OcrEngine(_settings())
        pdf = _make_pdf(
            ["SUPERMERCADO EL TIGRE", "RUC 20123456789", "Total: $123.45", "Fecha: 15/03/2026"]
        )
        receipt = engine.extract("recibo.pdf", "application/pdf", pdf)
        assert receipt.amount == Decimal("123.45")
        assert receipt.currency == "USD"
        assert receipt.date is not None
        assert receipt.date.year == 2026
        assert receipt.date.month == 3
        assert receipt.date.day == 15
        assert receipt.merchant == "SUPERMERCADO EL TIGRE"
        assert receipt.confidence == "high"

    def test_extract_image_without_tesseract_degrades(self) -> None:
        engine = OcrEngine(_settings())
        receipt = engine.extract("recibo.png", "image/png", b"not-a-real-image")
        assert receipt.amount is None
        assert any("OCR deshabilitado" in w for w in receipt.warnings)
        assert receipt.confidence == "low"

    def test_extract_unsupported_extension(self) -> None:
        engine = OcrEngine(_settings())
        with pytest.raises(ValueError):
            engine.extract("recibo.txt", "text/plain", b"hola")

    def test_extract_file_too_large(self) -> None:
        engine = OcrEngine(_settings(OCR_MAX_FILE_SIZE_MB=1))
        with pytest.raises(ValidationError):
            engine.extract("recibo.png", "image/png", b"x" * (1024 * 1024 + 1))
