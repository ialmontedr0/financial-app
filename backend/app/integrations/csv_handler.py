"""CSV import/export handler for transactions."""

from __future__ import annotations

import csv
import io
from typing import Any

import pandas as pd

EXPECTED_COLUMNS = {
    "date": ["date", "fecha", "effective_date", "transaction_date"],
    "description": ["description", "descripcion", "desc", "memo", "concepto"],
    "amount": ["amount", "monto", "importe", "valor"],
    "type": ["type", "tipo", "transaction_type", "tipo_transaccion"],
    "category": ["category", "categoria", "cat", "gategoria"],
    "account": ["account", "cuenta", "account_name"],
    "currency": ["currency", "moneda", "currency_code"],
    "notes": ["notes", "notas", "observaciones", "memo"],
}

VALID_TYPES = {"income", "expense", "transfer"}

TYPE_ALIASES = {
    "ingreso": "income",
    "gasto": "expense",
    "expense": "expense",
    "income": "income",
    "transfer": "transfer",
    "transferencia": "transfer",
    "debit": "expense",
    "credit": "income",
    "cargo": "expense",
    "abono": "income",
}


def normalize_column_name(col: str) -> str:
    """Normalize column name to match expected columns."""
    col_lower = col.strip().lower()
    for standard_name, aliases in EXPECTED_COLUMNS.items():
        if col_lower in aliases:
            return standard_name
    return col_lower


def parse_csv(file_content: bytes, encoding: str = "utf-8") -> pd.DataFrame:
    """Parse CSV content into a DataFrame with normalized columns."""
    text = None
    for enc in [encoding, "utf-8-sig", "latin-1", "cp1252"]:
        try:
            text = file_content.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if text is None:
        raise ValueError("Cannot decode CSV file. Unsupported encoding.")

    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(text[:4096])
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","

    df = pd.read_csv(
        io.StringIO(text),
        delimiter=delimiter,
        dtype=str,
        keep_default_na=False,
    )

    df.columns = [normalize_column_name(c) for c in df.columns]
    return df


def validate_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Validate each row and return list of errors."""
    errors: list[dict[str, Any]] = []

    required = ["date", "description", "amount"]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        errors.append({"row": 0, "field": "columns", "message": f"Missing columns: {missing_cols}"})
        return errors

    for idx, row in df.iterrows():
        row_num = idx + 2

        try:
            pd.to_datetime(row["date"])
        except (ValueError, TypeError):
            errors.append({"row": row_num, "field": "date", "message": f"Invalid date: {row['date']}"})

        try:
            amount_str = str(row["amount"]).replace(",", "").replace("$", "").replace("RD$", "").strip()
            amount = float(amount_str)
            if amount == 0:
                errors.append({"row": row_num, "field": "amount", "message": "Amount cannot be zero"})
        except (ValueError, TypeError):
            errors.append({"row": row_num, "field": "amount", "message": f"Invalid amount: {row['amount']}"})

        if "type" in df.columns:
            raw_type = str(row.get("type", "")).strip().lower()
            normalized_type = TYPE_ALIASES.get(raw_type, raw_type)
            if normalized_type not in VALID_TYPES:
                errors.append({"row": row_num, "field": "type", "message": f"Invalid type: {row.get('type', '')}"})

    return errors


def df_to_transactions(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert validated DataFrame rows to transaction dicts."""
    transactions = []

    for _, row in df.iterrows():
        amount_str = str(row["amount"]).replace(",", "").replace("$", "").replace("RD$", "").strip()
        amount = float(amount_str)

        raw_type = str(row.get("type", "expense")).strip().lower()
        normalized_type = TYPE_ALIASES.get(raw_type, raw_type)
        if normalized_type not in VALID_TYPES:
            normalized_type = "expense"

        if "type" not in df.columns or not str(row.get("type", "")).strip():
            if amount < 0:
                normalized_type = "expense"
                amount = abs(amount)
            else:
                normalized_type = "income"

        tx = {
            "date": str(row["date"]),
            "description": str(row["description"]).strip(),
            "amount": round(abs(amount), 2),
            "type": normalized_type,
            "category": str(row.get("category", "")).strip() or None,
            "account": str(row.get("account", "")).strip() or None,
            "currency": str(row.get("currency", "DOP")).strip() or "DOP",
            "notes": str(row.get("notes", "")).strip() or None,
        }
        transactions.append(tx)

    return transactions


def transactions_to_csv(transactions: list[dict[str, Any]]) -> str:
    """Convert transactions list to CSV string."""
    if not transactions:
        return ""

    output = io.StringIO()
    fieldnames = ["date", "description", "amount", "type", "category", "account", "currency", "notes"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(transactions)
    return output.getvalue()
