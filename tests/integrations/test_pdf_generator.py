"""PDF generator unit tests."""

import pytest


class TestPDFGenerator:
    def test_generate_transaction_report(self):
        from app.integrations.pdf_generator import generate_transaction_report

        txs = [
            {"date": "2024-01-15", "description": "Groceries", "amount": 50.0, "type": "expense", "category": "Food"},
            {"date": "2024-01-16", "description": "Salary", "amount": 3000.0, "type": "income"},
        ]
        pdf = generate_transaction_report(txs, title="Test Report")
        assert pdf.startswith(b"%PDF")
        assert len(pdf) > 100

    def test_generate_empty_report(self):
        from app.integrations.pdf_generator import generate_transaction_report

        pdf = generate_transaction_report([])
        assert pdf.startswith(b"%PDF")

    def test_generate_budget_report(self):
        from app.integrations.pdf_generator import generate_budget_report

        budgets = [
            {"category": "Food", "budget_amount": 1000, "spent_amount": 750},
            {"category": "Transport", "budget_amount": 500, "spent_amount": 300},
        ]
        pdf = generate_budget_report(budgets)
        assert pdf.startswith(b"%PDF")

    def test_generate_goals_report(self):
        from app.integrations.pdf_generator import generate_goals_report

        goals = [
            {"name": "Emergency Fund", "target_amount": 10000, "current_amount": 5000, "status": "active"},
        ]
        pdf = generate_goals_report(goals)
        assert pdf.startswith(b"%PDF")
