"""OCR domain value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

SUPPORTED_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"})
SUPPORTED_PDF_EXTENSION = ".pdf"
SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | frozenset({SUPPORTED_PDF_EXTENSION})

SUPPORTED_MIME_TYPES = frozenset(
    {
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/bmp",
        "image/tiff",
        "application/pdf",
    }
)

MAX_FILE_SIZE_MB = 10


@dataclass(frozen=True)
class ExtractedReceipt:
    """Datos estructurados extraidos de un recibo (OCR + regex)."""

    raw_text: str
    amount: Decimal | None = None
    date: date | None = None
    merchant: str | None = None
    currency: str | None = None
    confidence: str = "low"
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_complete(self) -> bool:
        return self.amount is not None and self.date is not None and self.merchant is not None

    @property
    def missing_fields(self) -> list[str]:
        missing: list[str] = []
        if self.amount is None:
            missing.append("amount")
        if self.date is None:
            missing.append("date")
        if self.merchant is None:
            missing.append("merchant")
        return missing


def validate_ocr_file(filename: str, content_type: str) -> None:
    """Valida extension y mime type de un archivo para OCR.

    Raises:
        ValueError: si la extension o el content type no estan soportados.
    """
    from pathlib import Path

    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"Extensión no soportada: {ext or '(sin extensión)'}. Soportado: {supported}"
        )
    if content_type and content_type.split(";")[0].strip() not in SUPPORTED_MIME_TYPES:
        raise ValueError(f"Tipo de archivo no soportado: {content_type}")
