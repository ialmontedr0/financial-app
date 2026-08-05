"""OCR engine: pytesseract + pdf2image con graceful degradation.

Si no esta disponible Tesseract/Poppler, o OCR_ENABLED=False, el motor
degrade a extraccion de texto (pypdf para PDFs textuales) + regex.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from app.core.config import get_settings
from app.domain.ocr.value_objects import ExtractedReceipt, validate_ocr_file
from app.middleware.error_handler import ValidationError

if TYPE_CHECKING:
    from app.core.config import Settings

logger = structlog.get_logger()

_MONEY_RE = re.compile(r"\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})")
_DATE_SEPARATOR_RE = re.compile(
    r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b"
)

_TOTAL_KEYWORDS = r"total|importe|monto|amount|a pagar|balance|grand total|total due"

_CURRENCY_MAP = {
    "S/": "PEN",
    "s/": "PEN",
    "$": "USD",
    "US$": "USD",
    "USD": "USD",
    "MXN": "MXN",
    "MX$": "MXN",
    "€": "EUR",
    "EUR": "EUR",
    "£": "GBP",
    "GBP": "GBP",
    "¥": "JPY",
    "JPY": "JPY",
    "COP": "COP",
    "ARS": "ARS",
    "BRL": "BRL",
    "PEN": "PEN",
}

_MONTHS_ES = r"enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre"
_MONTHS_EN = (
    r"january|february|march|april|may|june|july|august|september|october|november|december"
)
_MONTH_SHORT_EN = r"jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec"

_DATE_KEYWORDS = r"fecha|date|issued|emitted|emitido|comprado|purchase date"

_MERCHANT_KEYWORDS = (
    r"establecimiento|merchant|comercio|empresa|razon social|razón social|store|vendedor"
)

_MAX_TEXT_SNIPPET_LENGTH = 120


class OcrEngine:
    """Extrae texto e informacion financiera de imagenes y PDFs."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def extract(self, filename: str, content_type: str, data: bytes) -> ExtractedReceipt:
        validate_ocr_file(filename, content_type)
        if len(data) > self._settings.OCR_MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValidationError(
                f"El archivo supera el tamaño máximo de {self._settings.OCR_MAX_FILE_SIZE_MB} MB"
            )

        ext = Path(filename).suffix.lower()
        warnings: list[str] = []

        try:
            text = self._extract_text(ext, data, warnings)
        except ValidationError:
            raise
        except Exception as exc:
            logger.warning("ocr_engine_failed", error=str(exc), filename=filename)
            text = ""
            warnings.append("No se pudo procesar el archivo con el motor OCR.")

        amount, currency = self._parse_amount(text)
        parsed_date = self._parse_date(text)
        merchant = self._parse_merchant(text)

        if not text:
            warnings.append("No se pudo extraer texto del archivo.")
            confidence = "low"
        elif amount is None:
            warnings.append("No se pudo identificar un monto en el texto.")
            confidence = "low"
        else:
            confidence = "high" if parsed_date is not None and merchant else "medium"

        return ExtractedReceipt(
            raw_text=text[:8000],
            amount=amount,
            date=parsed_date,
            merchant=merchant,
            currency=currency,
            confidence=confidence,
            warnings=tuple(warnings),
        )

    # ------------------------------------------------------------------
    # Extraccion de texto
    # ------------------------------------------------------------------

    def _extract_text(self, ext: str, data: bytes, warnings: list[str]) -> str:
        if ext == ".pdf":
            return self._extract_pdf_text(data, warnings)
        return self._extract_image_text(data, warnings)

    def _extract_pdf_text(self, data: bytes, warnings: list[str]) -> str:
        if not self._settings.OCR_ENABLED:
            return self._extract_pdf_text_via_pypdf(data, warnings)

        try:
            from pdf2image import convert_from_bytes  # type: ignore[import-untyped]

            images = convert_from_bytes(data)
            if not images:
                warnings.append("El PDF no contiene páginas renderizables.")
                return self._extract_pdf_text_via_pypdf(data, warnings)
            return self._ocr_images(images, warnings)
        except Exception as exc:
            logger.debug("pdf2image_unavailable", error=str(exc))
            warnings.append(
                "No se pudo convertir el PDF a imagen; se intentó con texto incrustado."
            )
            return self._extract_pdf_text_via_pypdf(data, warnings)

    def _extract_pdf_text_via_pypdf(self, data: bytes, warnings: list[str]) -> str:
        try:
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(data))
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            text = "\n".join(pages)
            if not text.strip():
                warnings.append("El PDF no tiene texto incrustado (podría ser un escaneo).")
            return text
        except Exception as exc:
            logger.debug("pypdf_unavailable", error=str(exc))
            warnings.append("No se pudo leer el PDF.")
            return ""

    def _extract_image_text(self, data: bytes, warnings: list[str]) -> str:
        if not self._settings.OCR_ENABLED:
            warnings.append("OCR deshabilitado en la configuración.")
            return ""
        try:
            from PIL import Image
            from pytesseract import image_to_string
            from pytesseract.pytesseract import TesseractNotFoundError

            try:
                import pytesseract

                pytesseract.pytesseract.tesseract_cmd = self._settings.TESSERACT_CMD
            except Exception as exc:  # pragma: no cover - config fallida, usar default
                logger.debug("tesseract_cmd_config_failed", error=str(exc))

            with Image.open(BytesIO(data)) as img:
                try:
                    return image_to_string(img)
                except (TesseractNotFoundError, OSError) as exc:
                    logger.debug("tesseract_not_found", error=str(exc))
                    warnings.append("No se encontró el binario de Tesseract.")
                    return ""
        except (ImportError, OSError) as exc:
            logger.debug("ocr_deps_unavailable", error=str(exc))
            warnings.append("Dependencias OCR no disponibles (pytesseract/Pillow).")
            return ""
        except Exception as exc:
            logger.debug("image_ocr_failed", error=str(exc))
            warnings.append("No se pudo extraer texto de la imagen.")
            return ""

    def _ocr_images(self, images: list, warnings: list[str]) -> str:
        try:
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = self._settings.TESSERACT_CMD
            from pytesseract import image_to_string
            from pytesseract.pytesseract import TesseractNotFoundError

            pages = []
            for image in images:
                try:
                    pages.append(image_to_string(image))
                except (TesseractNotFoundError, OSError) as exc:
                    logger.debug("tesseract_not_found", error=str(exc))
                    warnings.append("No se encontró el binario de Tesseract.")
                    break
            return "\n".join(pages)
        except (ImportError, OSError) as exc:
            logger.debug("ocr_deps_unavailable", error=str(exc))
            warnings.append("Dependencias OCR no disponibles (pytesseract/Pillow).")
            return ""

    # ------------------------------------------------------------------
    # Parseo financiero
    # ------------------------------------------------------------------

    def _parse_amount(self, text: str) -> tuple[Decimal | None, str | None]:
        if not text:
            return None, None
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for line in lines:
            if re.search(_TOTAL_KEYWORDS, line, re.IGNORECASE):
                match = _MONEY_RE.search(line)
                if match and not self._looks_like_date_token(match.group(0)):
                    amount = self._to_decimal(match.group(0))
                    if amount is not None and amount > 0:
                        return amount, self._detect_currency(text)

        candidates: list[Decimal] = []
        for line in lines:
            if re.search(r"\$|S/|s/|€|£|¥|USD|EUR|MXN|COP|ARS|BRL|PEN", line, re.IGNORECASE):
                for match in _MONEY_RE.finditer(line):
                    token = match.group(0)
                    if not self._looks_like_date_token(token):
                        value = self._to_decimal(token)
                        if value is not None and value > 0:
                            candidates.append(value)
                            break

        if candidates:
            amount = max(candidates)
            return amount, self._detect_currency(text)

        return None, self._detect_currency(text)

    @staticmethod
    def _looks_like_date_token(token: str) -> bool:
        return bool(_DATE_SEPARATOR_RE.search(token))

    @staticmethod
    def _to_decimal(raw: str) -> Decimal | None:
        value = raw.strip()
        try:
            if "," in value and "." in value:
                if value.rfind(",") > value.rfind("."):
                    value = value.replace(".", "").replace(",", ".")
                else:
                    value = value.replace(",", "")
            elif "," in value:
                value = value.replace(",", ".")
            if value.count(".") > 1:
                value = value.replace(".", "", value.count(".") - 1)
            return Decimal(value)
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def _detect_currency(text: str) -> str | None:
        for symbol, code in _CURRENCY_MAP.items():
            if symbol in text:
                return code
        return None

    def _parse_date(self, text: str) -> date | None:
        if not text:
            return None

        keyword_lines = [
            line
            for line in text.splitlines()
            if re.search(_DATE_KEYWORDS, line, re.IGNORECASE)
            and re.search(_DATE_SEPARATOR_RE, line)
        ]
        for line in keyword_lines:
            parsed = self._first_date_in(line)
            if parsed is not None:
                return parsed

        parsed = self._first_date_in(text)
        if parsed is not None:
            return parsed

        return self._parse_month_name_date(text)

    @staticmethod
    def _first_date_in(text: str) -> date | None:
        match = re.search(
            r"\b(?P<d1>\d{1,2})[-/](?P<d2>\d{1,2})[-/](?P<y>\d{2,4})\b|\b(?P<y4>\d{4})[-/](?P<d3>\d{1,2})[-/](?P<d4>\d{1,2})\b",
            text,
        )
        if not match:
            return None
        try:
            if match.group("y4"):
                return date(int(match.group("y4")), int(match.group("d3")), int(match.group("d4")))
            year = int(match.group("y"))
            if year < 100:
                year += 2000 if year < 70 else 1900
            day, month = int(match.group("d1")), int(match.group("d2"))
            if month > 12:
                day, month = month, day
            return date(year, month, day)
        except ValueError:
            return None

    @staticmethod
    def _parse_month_name_date(text: str) -> date | None:
        month_map = {
            "enero": 1,
            "febrero": 2,
            "marzo": 3,
            "abril": 4,
            "mayo": 5,
            "junio": 6,
            "julio": 7,
            "agosto": 8,
            "septiembre": 9,
            "setiembre": 9,
            "octubre": 10,
            "noviembre": 11,
            "diciembre": 12,
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }
        month_re = r"(?:" + _MONTHS_ES + r"|" + _MONTHS_EN + r"|" + _MONTH_SHORT_EN + r")"
        day_first = re.compile(
            r"\b(\d{1,2})\s*(?:de\s+)?(" + month_re + r")[^\d]{0,4}(?:de\s+)?(\d{4})\b",
            re.IGNORECASE,
        )
        month_first = re.compile(
            r"\b(" + month_re + r")[^\d]{0,3}(?:de\s+)?(\d{1,2})[^\d]{0,4}(?:de\s+)?(\d{4})\b",
            re.IGNORECASE,
        )
        match = day_first.search(text) or month_first.search(text)
        if not match:
            return None
        try:
            group1, group2, year = match.group(1), match.group(2), int(match.group(3))
            if group1.isdigit():
                day, month_name = int(group1), group2.lower()
            else:
                day, month_name = int(group2), group1.lower()
            month = month_map.get(month_name)
            if month is None:
                return None
            return date(year, month, day)
        except (ValueError, TypeError):
            return None

    def _parse_merchant(self, text: str) -> str | None:
        if not text:
            return None
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for line in lines:
            if re.search(_MERCHANT_KEYWORDS, line, re.IGNORECASE):
                cleaned = re.sub(
                    r"(?i)\b(?:establecimiento|merchant|comercio|empresa|razon social|razón social|store|vendedor)\b[\s:]*",
                    "",
                    line,
                ).strip(" :;")
                cleaned = self._clean_merchant(cleaned)
                if cleaned:
                    return cleaned

        for line in lines:
            if len(line) > _MAX_TEXT_SNIPPET_LENGTH or len(line) < 3:
                continue
            if re.fullmatch(r"[\d\s.,()/$%-]+", line):
                continue
            if _DATE_SEPARATOR_RE.search(line):
                continue
            if re.search(_TOTAL_KEYWORDS, line, re.IGNORECASE):
                continue
            return self._clean_merchant(line)

        return None

    @staticmethod
    def _clean_merchant(line: str) -> str | None:
        cleaned = line.strip().strip(":;,.|-_").strip()
        if not cleaned or len(cleaned) < 3:
            return None
        return cleaned[:_MAX_TEXT_SNIPPET_LENGTH]
