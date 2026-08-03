"""Construye el propmpt del sistema con contexto financiero real."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime  # noqa: F401

SYSTEM_PROMPT_BASE = (
    "Eres el asistente financiero de FIP (Financial Intelligence Platform). "
    "Respondes en español de forma clara, concisa y útil. "
    "NUNCA inventes cifras: si no tienes datos, dilo. "
    "Usa la información de contexto proporcionada para responder."
)


class SystemPromptBuilder:
    """Compone el system prompt a partir de un contexto financiero agregado."""

    def build(self, context: dict) -> str:
        sections = [SYSTEM_PROMPT_BASE]

        accounts = context.get("accounts") or []
        if accounts:
            lines = [
                f"{a.get('name')}: {a.get('balance')} {a.get('currency', 'MXN')}" for a in accounts
            ]
            sections.append("### Cuentas (saldo actual)\n" + "\n".join(lines))

        budgets = context.get("budgets") or []
        if budgets:
            lines = [
                f"- {b.get('name')}: gastado {b.get('spent')} de {b.get('amount')} ({b.get('pct_used')}%)"
                for b in budgets
            ]
            sections.append("### Presupuestos del periodo actual\n" + "\n".join(lines))

        goals = context.get("goals") or []
        if goals:
            lines = [
                f"- {g.get('name')}: {g.get('progress_pct')}% alcanzado (meta {g.get('target_amount')})"
                for g in goals
            ]
            sections.append("### Metas financieras\n" + "\n".join(lines))

        transactions = context.get("recent_transactions") or []
        if transactions:
            lines = [
                f"- {t.get('date')} {t.get('description')}: {t.get('amount')} {t.get('currency', 'MXN')} ({t.get('type')})"
                for t in transactions
            ]
            sections.append("### Últimas transacciones\n" + "\n".join(lines))

        if context.get("today"):
            sections.append(f"### Fecha de hoy: {context.get('today')}")

        return "\n\n".join(sections)
