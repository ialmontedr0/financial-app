"""CSV handler unit tests."""

import pytest


class TestCSVHandler:
    def test_normalize_column_name(self):
        from app.integrations.csv_handler import normalize_column_name

        assert normalize_column_name("Fecha") == "date"
        assert normalize_column_name("descripcion") == "description"
        assert normalize_column_name("monto") == "amount"
        assert normalize_column_name("tipo") == "type"
        assert normalize_column_name("custom_col") == "custom_col"

    def test_parse_csv_basic(self):
        from app.integrations.csv_handler import parse_csv

        csv_content = b"date,description,amount,type\n2024-01-15,Groceries,50.00,expense\n2024-01-16,Salary,3000.00,income"
        df = parse_csv(csv_content)
        assert len(df) == 2
        assert "date" in df.columns
        assert "amount" in df.columns

    def test_validate_rows_valid(self):
        from app.integrations.csv_handler import parse_csv, validate_rows

        csv_content = b"date,description,amount\n2024-01-15,Groceries,50.00"
        df = parse_csv(csv_content)
        errors = validate_rows(df)
        assert len(errors) == 0

    def test_validate_rows_invalid_date(self):
        from app.integrations.csv_handler import parse_csv, validate_rows

        csv_content = b"date,description,amount\nnot-a-date,Groceries,50.00"
        df = parse_csv(csv_content)
        errors = validate_rows(df)
        assert len(errors) == 1
        assert errors[0]["field"] == "date"

    def test_validate_rows_invalid_amount(self):
        from app.integrations.csv_handler import parse_csv, validate_rows

        csv_content = b"date,description,amount\n2024-01-15,Groceries,abc"
        df = parse_csv(csv_content)
        errors = validate_rows(df)
        assert len(errors) == 1
        assert errors[0]["field"] == "amount"

    def test_transactions_to_csv(self):
        from app.integrations.csv_handler import transactions_to_csv

        txs = [{"date": "2024-01-15", "description": "Test", "amount": 50.0, "type": "expense"}]
        csv_str = transactions_to_csv(txs)
        assert "date" in csv_str
        assert "Test" in csv_str

    def test_type_aliases(self):
        from app.integrations.csv_handler import df_to_transactions, parse_csv

        csv_content = b"date,description,amount,type\n2024-01-15,Groceries,50.00,ingreso"
        df = parse_csv(csv_content)
        txs = df_to_transactions(df)
        assert txs[0]["type"] == "income"
