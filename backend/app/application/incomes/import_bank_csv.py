"""Use case: Import incomes from bank CSV data."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.application.incomes.create_income_bulk import CreateIncomeBulkUseCase

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ImportBankCSVUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._bulk_uc = CreateIncomeBulkUseCase(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        rows: list[dict],
        default_account_id: uuid.UUID | None = None,
    ) -> dict:
        from app.middleware.error_handler import ValidationError

        if not rows:
            raise ValidationError("CSV vacio, no hay filas para importar")

        incomes: list[dict] = []
        skipped = 0

        for i, row in enumerate(rows):
            try:
                amount = row.get("amount") or row.get("monto") or row.get("Amount") or row.get("Monto")
                description = row.get("description") or row.get("descripcion") or row.get("Description") or row.get("Descripcion") or row.get("concept")
                effective_date = row.get("date") or row.get("fecha") or row.get("Date") or row.get("Fecha") or row.get("effective_date")
                transaction_type = (row.get("transaction_type") or row.get("tipo") or "").lower()

                if transaction_type and transaction_type not in ("credit", "income", "abono", "ingreso", "deposit"):
                    skipped += 1
                    continue

                if not transaction_type and amount:
                    try:
                        if float(str(amount).replace(",", "")) < 0:
                            skipped += 1
                            continue
                    except (ValueError, TypeError):
                        pass

                if not amount or not description or not effective_date:
                    logger.warning("csv_row_missing_fields", row_index=i)
                    skipped += 1
                    continue

                account_id = row.get("account_id") or row.get("cuenta_id")
                if not account_id:
                    if default_account_id:
                        account_id = str(default_account_id)
                    else:
                        logger.warning("csv_row_no_account", row_index=i)
                        skipped += 1
                        continue

                clean_amount = str(abs(float(str(amount).replace(",", ""))))

                incomes.append({
                    "account_id": account_id,
                    "amount": clean_amount,
                    "description": str(description),
                    "effective_date": str(effective_date),
                    "category_id": row.get("category_id"),
                    "notes": row.get("notes") or row.get("notas"),
                    "source": "bank_import",
                    "currency_code": row.get("currency_code") or "DOP",
                    "income_type": "other",
                    "income_status": "received",
                    "stability": "one_time",
                })
            except Exception as e:
                logger.warning("csv_row_parse_error", row_index=i, error=str(e))
                skipped += 1
                continue

        if not incomes:
            raise ValidationError("No se pudieron parsear filas validas de ingresos del CSV")

        result = await self._bulk_uc.execute(user_id, incomes)
        logger.info("bank_csv_import_completed", user_id=str(user_id), created=result["created"], errors=result["errors"], skipped=skipped)

        return {
            "imported": result["created"],
            "errors": result["errors"],
            "skipped": skipped,
            "total_rows": len(rows),
            "incomes": result["incomes"],
            "error_details": result["error_details"],
        }
