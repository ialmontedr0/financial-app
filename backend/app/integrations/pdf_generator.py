"""PDF report generator for financial data."""

from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _get_styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "CustomTitle",
            parent=styles["Title"],
            fontSize=20,
            spaceAfter=20,
            textColor=colors.HexColor("#1a1a2e"),
        ),
        "subtitle": ParagraphStyle(
            "CustomSubtitle",
            parent=styles["Heading2"],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.HexColor("#16213e"),
        ),
        "normal": ParagraphStyle(
            "CustomNormal",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "CustomSmall",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
        ),
        "right": ParagraphStyle(
            "CustomRight",
            parent=styles["Normal"],
            fontSize=10,
            alignment=TA_RIGHT,
        ),
    }


def _format_currency(amount: float, currency: str = "DOP") -> str:
    symbols = {"DOP": "RD$", "USD": "$", "EUR": "\u20ac", "GBP": "\u00a3"}
    symbol = symbols.get(currency, currency + " ")
    return f"{symbol}{amount:,.2f}"


def _build_table(
    headers: list[str], rows: list[list[str]], col_widths: list[float] | None = None
) -> Table:
    data = [headers, *rows]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B579A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f0f0")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
    ]))
    return table


def generate_transaction_report(
    transactions: list[dict[str, Any]],
    title: str = "Transaction Report",
    user_email: str = "",
    date_from: str = "",
    date_to: str = "",
) -> bytes:
    """Generate a PDF report of transactions."""
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    styles = _get_styles()
    elements: list[Any] = []

    elements.append(Paragraph(title, styles["title"]))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#2B579A")))

    meta_parts = []
    if user_email:
        meta_parts.append(f"User: {user_email}")
    if date_from:
        meta_parts.append(f"From: {date_from}")
    if date_to:
        meta_parts.append(f"To: {date_to}")
    meta_parts.append(f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
    elements.append(Paragraph(" | ".join(meta_parts), styles["small"]))
    elements.append(Spacer(1, 12))

    total_income = sum(t["amount"] for t in transactions if t.get("type") == "income")
    total_expense = sum(t["amount"] for t in transactions if t.get("type") == "expense")
    net = total_income - total_expense

    elements.append(Paragraph("Summary", styles["subtitle"]))
    summary_data = [
        ["Total Income", _format_currency(total_income)],
        ["Total Expenses", _format_currency(total_expense)],
        ["Net Flow", _format_currency(net)],
        ["Total Transactions", str(len(transactions))],
    ]
    summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Transactions", styles["subtitle"]))
    headers = ["Date", "Description", "Type", "Category", "Amount"]
    rows = []
    for tx in transactions:
        rows.append([
            tx.get("date", ""),
            tx.get("description", "")[:40],
            tx.get("type", ""),
            tx.get("category", "") or "-",
            _format_currency(tx.get("amount", 0)),
        ])

    if rows:
        table = _build_table(
            headers, rows, col_widths=[1.2 * inch, 2.5 * inch, 1 * inch, 1.2 * inch, 1.3 * inch]
        )
        elements.append(table)
    else:
        elements.append(Paragraph("No transactions found.", styles["normal"]))

    doc.build(elements)
    output.seek(0)
    return output.getvalue()


def generate_budget_report(
    budgets: list[dict[str, Any]],
    title: str = "Budget Report",
    user_email: str = "",
) -> bytes:
    """Generate a PDF budget vs actual report."""
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    styles = _get_styles()
    elements: list[Any] = []

    elements.append(Paragraph(title, styles["title"]))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#2B579A")))

    meta = f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}"
    if user_email:
        meta = f"User: {user_email} | {meta}"
    elements.append(Paragraph(meta, styles["small"]))
    elements.append(Spacer(1, 12))

    headers = ["Category", "Budget", "Spent", "Remaining", "Usage %"]
    rows = []
    for b in budgets:
        budget_amt = b.get("budget_amount", 0)
        spent = b.get("spent_amount", 0)
        remaining = budget_amt - spent
        usage_pct = (spent / budget_amt * 100) if budget_amt > 0 else 0
        rows.append([
            b.get("category", ""),
            _format_currency(budget_amt),
            _format_currency(spent),
            _format_currency(remaining),
            f"{usage_pct:.1f}%",
        ])

    if rows:
        table = _build_table(
            headers, rows, col_widths=[1.5 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1 * inch]
        )
        elements.append(table)
    else:
        elements.append(Paragraph("No budget data found.", styles["normal"]))

    doc.build(elements)
    output.seek(0)
    return output.getvalue()


def generate_goals_report(
    goals: list[dict[str, Any]],
    title: str = "Financial Goals Report",
    user_email: str = "",
) -> bytes:
    """Generate a PDF goals progress report."""
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    styles = _get_styles()
    elements: list[Any] = []

    elements.append(Paragraph(title, styles["title"]))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#2B579A")))

    meta = f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}"
    if user_email:
        meta = f"User: {user_email} | {meta}"
    elements.append(Paragraph(meta, styles["small"]))
    elements.append(Spacer(1, 12))

    headers = ["Goal", "Target", "Current", "Progress", "Status"]
    rows = []
    for g in goals:
        target = g.get("target_amount", 0)
        current = g.get("current_amount", 0)
        progress = (current / target * 100) if target > 0 else 0
        rows.append([
            g.get("name", "")[:30],
            _format_currency(target),
            _format_currency(current),
            f"{progress:.1f}%",
            g.get("status", "active"),
        ])

    if rows:
        table = _build_table(
            headers, rows, col_widths=[1.8 * inch, 1.2 * inch, 1.2 * inch, 1 * inch, 1 * inch]
        )
        elements.append(table)
    else:
        elements.append(Paragraph("No goals found.", styles["normal"]))

    doc.build(elements)
    output.seek(0)
    return output.getvalue()
