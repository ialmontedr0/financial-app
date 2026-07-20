"""Use case: Import expenses from CSV data."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.application.expenses.create_expense_bulk import CreateExpenseBulkUseCase

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ImportCSVUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._bulk_uc = CreateExpenseBulkUseCase(session)

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

        # Normalize CSV rows to expense format
        expenses: list[dict] = []
        for i, row in enumerate(rows):
            try:
                # Support common CSV column names
                amount = (
                    row.get("amount") or row.get("monto") or row.get("Amount") or row.get("Monto")
                )
                description = (
                    row.get("description")
                    or row.get("descripcion")
                    or row.get("Description")
                    or row.get("Descripcion")
                    or row.get("memo")
                    or row.get("concept")
                )
                effective_date = (
                    row.get("date")
                    or row.get("fecha")
                    or row.get("Date")
                    or row.get("Fecha")
                    or row.get("effective_date")
                )
                category = row.get("category") or row.get("categoria") or row.get("Category")
                notes = row.get("notes") or row.get("notas") or row.get("Notes")

                if not amount or not description or not effective_date:
                    raise ValidationError(
                        f"Fila {i + 1}: amount, description y date son requeridos"
                    )

                account_id = row.get("account_id") or row.get("cuenta_id")
                if not account_id:
                    if default_account_id:
                        account_id = str(default_account_id)
                    else:
                        raise ValidationError(f"Fila {i + 1}: account_id es requerido")

                expenses.append(
                    {
                        "account_id": account_id,
                        "amount": str(amount),
                        "description": str(description),
                        "effective_date": str(effective_date),
                        "category_id": str(category) if category else None,
                        "notes": str(notes) if notes else None,
                        "source": "import",
                        "currency_code": row.get("currency_code") or "DOP",
                    }
                )
            except ValidationError:
                raise
            except Exception as e:
                logger.warning("csv_row_parse_error", row_index=i, error=str(e))
                continue

        if not expenses:
            raise ValidationError("No se pudieron parsear filas validas del CSV")

        result = await self._bulk_uc.execute(user_id, expenses)
        logger.info(
            "csv_import_completed",
            user_id=str(user_id),
            created=result["created"],
            errors=result["errors"],
        )

        return {
            "imported": result["created"],
            "errors": result["errors"],
            "total_rows": len(rows),
            "transactions": result["transactions"],
            "error_details": result["error_details"],
        }
