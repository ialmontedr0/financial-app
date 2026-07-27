"""Modern PDF report generator for financial data."""

from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Brand Palette ──────────────────────────────────────────
PURPLE = "#7c3aed"
INDIGO = "#4f46e5"
DARK_HEADER = "#1e1b4b"
EMERALD = "#10b981"
RED = "#ef4444"
AMBER = "#f59e0b"
GRAY_50 = "#f9fafb"
GRAY_100 = "#f3f4f6"
GRAY_200 = "#e5e7eb"
GRAY_400 = "#9ca3af"
GRAY_500 = "#6b7280"
WHITE = "#ffffff"


# ── Helpers ────────────────────────────────────────────────


def _format_currency(amount: float, currency: str = "DOP") -> str:
    symbols = {"DOP": "RD$", "USD": "$", "EUR": "\u20ac", "GBP": "\u00a3"}
    symbol = symbols.get(currency, currency + " ")
    if amount < 0:
        return f'<font color="{RED}">({symbol}{abs(amount):,.2f})</font>'
    return f"{symbol}{amount:,.2f}"


def _style(name: str, **kw) -> ParagraphStyle:
    return ParagraphStyle(name, **kw)


def _header_block(title: str, subtitle: str = "") -> list:
    """Dark gradient header with accent underline."""
    lines = [
        [
            Paragraph(
                f'<font color="{WHITE}" size="18"><b>{title}</b></font>',
                _style("ht", alignment=TA_LEFT),
            )
        ],
    ]
    if subtitle:
        lines.append(
            [
                Paragraph(
                    f'<font color="#a78bfa" size="9">{subtitle}</font>',
                    _style("hs", alignment=TA_LEFT),
                )
            ],
        )
    t = Table(lines, colWidths=[6.5 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(DARK_HEADER)),
                ("TOPPADDING", (0, 0), (-1, 0), 18),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
                ("LEFTPADDING", (0, 0), (-1, -1), 22),
                ("RIGHTPADDING", (0, 0), (-1, -1), 22),
                ("LINEBELOW", (0, -1), (-1, -1), 3, colors.HexColor(PURPLE)),
            ]
        )
    )
    return [t, Spacer(1, 14)]


def _meta_bar(*parts: str) -> list:
    """Light-gray bar with metadata."""
    html = " &nbsp;\u00b7&nbsp; ".join(
        f'<font color="{GRAY_500}">{p}</font>' for p in parts
    )
    t = Table(
        [[Paragraph(html, _style("mb", fontSize=7, alignment=TA_LEFT))]],
        colWidths=[6.5 * inch],
    )
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(GRAY_50)),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor(GRAY_200)),
            ]
        )
    )
    return [t, Spacer(1, 14)]


def _kpi_cards(*cards: dict) -> list:
    """Row of summary cards with colored backgrounds."""
    n = len(cards)
    cw = 6.5 / n
    row = []
    for card in cards:
        row.append(
            Paragraph(
                f'<font color="{card["color"]}" size="16"><b>{card["value"]}</b></font>'
                f"<br/>"
                f'<font color="{GRAY_500}" size="7">{card["label"]}</font>',
                _style("kpi", alignment=TA_CENTER, leading=20),
            )
        )
    t = Table([row], colWidths=[cw * inch] * n)
    s = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]
    for i, c in enumerate(cards):
        s.append(("BACKGROUND", (i, 0), (i, 0), colors.HexColor(c.get("bg", WHITE))))
        if i < n - 1:
            s.append(("LINEAFTER", (i, 0), (i, 0), 1, colors.HexColor(GRAY_200)))
    t.setStyle(TableStyle(s))
    return [t, Spacer(1, 14)]


def _section_title(text: str) -> list:
    """Accent-underline section heading."""
    t = Table(
        [[Paragraph(f'<font color="{PURPLE}" size="11"><b>{text}</b></font>', _style("st"))]],
        colWidths=[6.5 * inch],
    )
    t.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, 0), 2, colors.HexColor(PURPLE)),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
            ]
        )
    )
    return [Spacer(1, 2), t, Spacer(1, 6)]


def _data_table(headers: list[str], rows: list[list], col_widths: list[float]) -> Table:
    """Modern table with dark header, zebra body, accent bottom border."""
    data = [headers, *rows]
    t = Table(data, colWidths=[w * inch for w in col_widths], repeatRows=1)
    s = [
        # header
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK_HEADER)),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        # body
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("TOPPADDING", (0, 1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#f8fafc")]),
        # accent bottom
        ("LINEBELOW", (0, -1), (-1, -1), 2, colors.HexColor(PURPLE)),
    ]
    # vertical separators
    for i in range(len(headers) - 1):
        s.append(("LINEAFTER", (i, 0), (i, -1), 0.3, colors.HexColor(GRAY_200)))
    t.setStyle(TableStyle(s))
    return t


def _footer(canvas, doc):
    """Page-number footer."""
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor(GRAY_200))
    canvas.setLineWidth(0.5)
    y = 0.52 * inch
    canvas.line(doc.leftMargin, y, doc.width + doc.leftMargin, y)
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(colors.HexColor(GRAY_400))
    canvas.drawString(
        doc.leftMargin, y - 12,
        f"Generated {datetime.now(UTC).strftime('%b %d, %Y at %H:%M UTC')}",
    )
    canvas.drawRightString(
        doc.width + doc.leftMargin, y - 12,
        f"Page {doc.page}",
    )
    canvas.restoreState()


# ── Public generators ──────────────────────────────────────


def generate_transaction_report(
    transactions: list[dict[str, Any]],
    title: str = "Transaction Report",
    user_email: str = "",
    date_from: str = "",
    date_to: str = "",
) -> bytes:
    """Modern transaction report with KPI cards and detail table."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=0.45 * inch, bottomMargin=0.75 * inch,
        leftMargin=0.55 * inch, rightMargin=0.55 * inch,
    )
    el: list[Any] = []

    # ── header ──
    subtitle = ""
    if date_from and date_to:
        subtitle = f"{date_from}  \u2192  {date_to}"
    elif date_from:
        subtitle = f"From {date_from}"
    elif date_to:
        subtitle = f"Until {date_to}"
    el.extend(_header_block(title, subtitle))

    # ── meta ──
    parts = [f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}"]
    if user_email:
        parts.append(f"User: {user_email}")
    parts.append(f"{len(transactions)} transactions")
    el.extend(_meta_bar(*parts))

    # ── KPI cards ──
    income = sum(t["amount"] for t in transactions if t.get("type") == "income")
    expense = sum(t["amount"] for t in transactions if t.get("type") == "expense")
    net = income - expense
    el.extend(
        _kpi_cards(
            {"label": "Total Income", "value": _format_currency(income),
             "color": EMERALD, "bg": "#f0fdf4"},
            {"label": "Total Expenses", "value": _format_currency(expense),
             "color": RED, "bg": "#fef2f2"},
            {"label": "Net Flow", "value": _format_currency(net),
             "color": EMERALD if net >= 0 else RED, "bg": "#f8fafc"},
            {"label": "Transactions", "value": str(len(transactions)),
             "color": PURPLE, "bg": "#f5f3ff"},
        )
    )

    # ── detail table ──
    el.extend(_section_title("Transaction Details"))
    headers = ["Date", "Description", "Type", "Category", "Amount"]
    rows = []
    for tx in transactions:
        amt = tx.get("amount", 0)
        display_amt = _format_currency(-amt) if tx.get("type") == "expense" else _format_currency(amt)
        rows.append([
            Paragraph(f'<font size="7">{tx.get("date", "")}</font>', _style("c")),
            Paragraph(f'<font size="7">{tx.get("description", "")[:55]}</font>', _style("c")),
            Paragraph(f'<font size="7">{tx.get("type", "")}</font>', _style("c")),
            Paragraph(f'<font size="7">{tx.get("category", "-")}</font>', _style("c")),
            Paragraph(f'<font size="7">{display_amt}</font>', _style("ca", alignment=TA_RIGHT)),
        ])

    if rows:
        el.append(_data_table(headers, rows, [0.95, 2.4, 0.75, 0.95, 1.45]))
    else:
        el.append(Paragraph("No transactions found.", _style("empty", fontSize=9, textColor=colors.HexColor(GRAY_400))))

    doc.build(el, onFirstPage=_footer, onLaterPages=_footer)
    buf.seek(0)
    return buf.getvalue()


def generate_budget_report(
    budgets: list[dict[str, Any]],
    title: str = "Budget Report",
    user_email: str = "",
) -> bytes:
    """Modern budget-vs-actual report with usage colour-coding."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=0.45 * inch, bottomMargin=0.75 * inch,
        leftMargin=0.55 * inch, rightMargin=0.55 * inch,
    )
    el: list[Any] = []

    el.extend(_header_block(title))
    parts = [f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}"]
    if user_email:
        parts.append(f"User: {user_email}")
    parts.append(f"{len(budgets)} categories")
    el.extend(_meta_bar(*parts))

    total_budget = sum(b.get("budget_amount", 0) for b in budgets)
    total_spent = sum(b.get("spent_amount", 0) for b in budgets)
    pct = (total_spent / total_budget * 100) if total_budget else 0
    remaining = total_budget - total_spent

    pct_color = EMERALD if pct < 75 else (AMBER if pct < 90 else RED)
    el.extend(
        _kpi_cards(
            {"label": "Total Budget", "value": _format_currency(total_budget),
             "color": PURPLE, "bg": "#f5f3ff"},
            {"label": "Total Spent", "value": _format_currency(total_spent),
             "color": INDIGO, "bg": "#eef2ff"},
            {"label": "Remaining", "value": _format_currency(remaining),
             "color": EMERALD if remaining >= 0 else RED,
             "bg": "#f0fdf4" if remaining >= 0 else "#fef2f2"},
            {"label": "Usage", "value": f"{pct:.1f}%",
             "color": pct_color, "bg": "#f8fafc"},
        )
    )

    el.extend(_section_title("Budget vs. Actual"))
    headers = ["Category", "Budget", "Spent", "Remaining", "Usage"]
    rows = []
    for b in budgets:
        ba = b.get("budget_amount", 0)
        sp = b.get("spent_amount", 0)
        rm = ba - sp
        up = (sp / ba * 100) if ba else 0
        uc = EMERALD if up < 75 else (AMBER if up < 90 else RED)
        rows.append([
            Paragraph(f'<font size="7">{b.get("category", "")}</font>', _style("c")),
            Paragraph(f'<font size="7">{_format_currency(ba)}</font>', _style("cr", alignment=TA_RIGHT)),
            Paragraph(f'<font size="7">{_format_currency(sp)}</font>', _style("cr", alignment=TA_RIGHT)),
            Paragraph(f'<font color="{EMERALD if rm >= 0 else RED}" size="7">{_format_currency(rm)}</font>',
                      _style("cr", alignment=TA_RIGHT)),
            Paragraph(f'<font color="{uc}" size="7"><b>{up:.1f}%</b></font>',
                      _style("cr", alignment=TA_RIGHT)),
        ])

    if rows:
        el.append(_data_table(headers, rows, [1.55, 1.2, 1.2, 1.2, 1.35]))
    else:
        el.append(Paragraph("No budget data found.", _style("empty", fontSize=9, textColor=colors.HexColor(GRAY_400))))

    doc.build(el, onFirstPage=_footer, onLaterPages=_footer)
    buf.seek(0)
    return buf.getvalue()


def generate_goals_report(
    goals: list[dict[str, Any]],
    title: str = "Financial Goals Report",
    user_email: str = "",
) -> bytes:
    """Modern goals-progress report with status badges."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=0.45 * inch, bottomMargin=0.75 * inch,
        leftMargin=0.55 * inch, rightMargin=0.55 * inch,
    )
    el: list[Any] = []

    el.extend(_header_block(title))
    parts = [f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}"]
    if user_email:
        parts.append(f"User: {user_email}")
    parts.append(f"{len(goals)} goals")
    el.extend(_meta_bar(*parts))

    total_target = sum(g.get("target_amount", 0) for g in goals)
    total_current = sum(g.get("current_amount", 0) for g in goals)
    overall = (total_current / total_target * 100) if total_target else 0
    completed = sum(1 for g in goals if g.get("status") == "completed")
    active = len(goals) - completed
    oc = EMERALD if overall >= 75 else (AMBER if overall >= 40 else PURPLE)

    el.extend(
        _kpi_cards(
            {"label": "Total Target", "value": _format_currency(total_target),
             "color": PURPLE, "bg": "#f5f3ff"},
            {"label": "Total Saved", "value": _format_currency(total_current),
             "color": EMERALD, "bg": "#f0fdf4"},
            {"label": "Progress", "value": f"{overall:.1f}%",
             "color": oc, "bg": "#f8fafc"},
            {"label": f"{completed} done \u00b7 {active} active",
             "value": f"{completed + active}",
             "color": INDIGO, "bg": "#eef2ff"},
        )
    )

    el.extend(_section_title("Goal Details"))
    headers = ["Goal", "Target", "Current", "Progress", "Status"]
    rows = []
    for g in goals:
        target = g.get("target_amount", 0)
        current = g.get("current_amount", 0)
        prog = (current / target * 100) if target else 0
        status = g.get("status", "active")
        sc = {"completed": EMERALD, "active": PURPLE, "on_track": INDIGO,
              "at_risk": AMBER, "failed": RED}.get(status, GRAY_500)
        pc = EMERALD if prog >= 75 else (AMBER if prog >= 40 else RED)
        rows.append([
            Paragraph(f'<font size="7">{g.get("name", "")[:35]}</font>', _style("c")),
            Paragraph(f'<font size="7">{_format_currency(target)}</font>', _style("cr", alignment=TA_RIGHT)),
            Paragraph(f'<font size="7">{_format_currency(current)}</font>', _style("cr", alignment=TA_RIGHT)),
            Paragraph(f'<font color="{pc}" size="7"><b>{prog:.1f}%</b></font>',
                      _style("cr", alignment=TA_RIGHT)),
            Paragraph(f'<font color="{sc}" size="7"><b>{status.upper()}</b></font>',
                      _style("c", alignment=TA_CENTER)),
        ])

    if rows:
        el.append(_data_table(headers, rows, [1.55, 1.2, 1.2, 1.0, 1.55]))
    else:
        el.append(Paragraph("No goals found.", _style("empty", fontSize=9, textColor=colors.HexColor(GRAY_400))))

    doc.build(el, onFirstPage=_footer, onLaterPages=_footer)
    buf.seek(0)
    return buf.getvalue()
