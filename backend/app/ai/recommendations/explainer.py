"""Personalized explainer — generates natural language explanations."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import LLMClient, SYSTEM_PROMPT_EXPLANATION, USER_PROMPT_EXPLANATION
from app.infrastructure.models.transaction import TransactionModel
from app.infrastructure.models.user_preference import UserPreferenceModel

logger = structlog.get_logger()

# Cache simple en memoria: {cache_key: (timestamp, response)}
_EXPLANATION_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL_SECONDS = 3600

# Spanish language templates (fallback cuando LLM no esta disponible)
EXPLANATION_TEMPLATES: dict[str, dict[str, str]] = {
    "reduce_spending": {
        "headline": "Tu gasto ha aumentado significativamente.",
        "why": (
            "Has gastado {amount:.0f} este mes, lo cual es un {pct:.0f}% "
            "por encima de tu promedio de {avg:.0f}/mes de los ultimos 3 meses."
        ),
        "how": (
            "Revisa tu categoria de '{category}' que concentra el "
            "{cat_share:.0f}% de tu gasto total."
        ),
        "impact": (
            "Si reduces este gasto en un 15%, podrias ahorrar "
            "~{savings:.0f} mensuales, lo que equivale a {annual:.0f} anuales."
        ),
        "action": "Identifica las transacciones mas altas en esta categoria y busca alternativas.",
    },
    "increase_savings": {
        "headline": "Tu tasa de ahorro esta por debajo del recomendado.",
        "why": (
            "De un ingreso de {income:.0f}, ahorras {savings:.0f} "
            "({rate:.1f}%). El recomendado es 20%."
        ),
        "how": (
            "Necesitas incrementar tu ahorro mensual en {gap:.0f} para alcanzar el 20% recomendado."
        ),
        "impact": (
            "Ahorrar {gap:.0f}/mes te daria {annual:.0f} anuales, "
            "suficiente para tu fondo de emergencia en {months:.0f} meses."
        ),
        "action": "Reduce gastos discrecionales o busca fuentes de ingreso adicionales.",
    },
    "build_emergency_fund": {
        "headline": "Tu fondo de emergencia es insuficiente.",
        "why": (
            "Actualmente tienes {balance:.0f} que cubre {months:.1f} meses "
            "de gastos. Se recomiendan 6 meses."
        ),
        "how": ("Necesitas {gap:.0f} adicionales para alcanzar 6 meses de gastos ({target:.0f})."),
        "impact": (
            "Un fondo adecuado te protege contra imprevistos como "
            "perdida de empleo o gastos medicos urgentes."
        ),
        "action": (
            "Transfiere {monthly:.0f}/mes a una cuenta de ahorro dedicada hasta completar el fondo."
        ),
    },
    "cancel_subscription": {
        "headline": "Tienes suscripciones costosas.",
        "why": (
            "La suscripcion '{name}' cuesta {cost:.0f}/mes "
            "({annual:.0f}/ano), lo cual es alto para tu presupuesto."
        ),
        "how": (
            "El total de tus suscripciones es {total:.0f}/mes, "
            "representando el {pct:.1f}% de tus ingresos."
        ),
        "impact": ("Cancelar esta suscripcion te ahorraría {annual:.0f} anuales."),
        "action": "Evalua si usas esta suscripcion lo suficiente para justificar el costo.",
    },
    "spending_pattern": {
        "headline": "Tu patron de gasto tiene areas de mejora.",
        "why": (
            "El {pct:.0f}% de tu gasto ocurre en fin de semana, "
            "con un promedio de {avg:.0f} por transaccion."
        ),
        "how": ("Los fines de semana tiendes a gastar mas en entretenimiento y restaurantes."),
        "impact": ("Reducir el gasto de fin de semana en un 15% ahorraría ~{savings:.0f}/mes."),
        "action": "Planifica actividades de bajo costo para los fines de semana.",
    },
    "debt_strategy": {
        "headline": "Puedes optimizar el pago de tus deudas.",
        "why": (
            "Con la estrategia {strategy}, podrias ahorrar {savings:.0f} en intereses totales."
        ),
        "how": (
            "Prioriza pagar primero la deuda con mayor tasa de interes "
            "({rate:.1f}%) mientras mantienes los pagos minimos en las demas."
        ),
        "impact": ("Esto reducira tu tiempo total de pago y el monto total de intereses."),
        "action": "Haz un listado de todas tus deudas ordenadas por tasa de interes.",
    },
    "savings_allocation": {
        "headline": "Tienes metas financieras activas.",
        "why": ("Tienes {count} metas activas con una necesidad total de {total:.0f}/mes."),
        "how": ("La meta prioritaria es '{goal}' que requiere {amount:.0f}/mes."),
        "impact": (
            "Seguir este plan te permitira alcanzar tus metas en el orden de prioridad establecido."
        ),
        "action": "Configura transferencias automaticas para cada meta.",
    },
    "budget_adjustment": {
        "headline": "Uno de tus presupuestos esta al limite.",
        "why": ("El presupuesto '{name}' esta al {pct:.0f}% de uso ({spent:.0f} de {limit:.0f})."),
        "how": ("Te quedan {remaining:.0f} para el resto del periodo."),
        "impact": (
            "Si excedes el presupuesto, podrias generar deuda o descuidar otros gastos importantes."
        ),
        "action": "Reduce gastos en esta categoria o ajusta el monto del presupuesto.",
    },
    "optimize_categories": {
        "headline": "Una categoria concentra demasiado tu gasto.",
        "why": (
            "El {pct:.0f}% de tu gasto va a '{category}' ({amount:.0f} en {count} transacciones)."
        ),
        "how": (
            "Una alta concentracion en una categoria puede indicar "
            "gasto excesivo o falta de diversificacion."
        ),
        "impact": ("Reducir este gasto en un 10% ahorraría ~{savings:.0f}/mes."),
        "action": "Revisa las transacciones en esta categoria y busca areas de reduccion.",
    },
    "habit_optimization": {
        "headline": "Tu gasto es inestable.",
        "why": ("Tu gasto mensual fluctua mucho (CV: {cv:.2f}). Esto dificulta el planeamiento."),
        "how": (
            "Establecer un presupuesto fijo para esta categoria te ayudara a controlar el gasto."
        ),
        "impact": ("Un gasto mas predecible te permite ahorrar de manera mas efectiva."),
        "action": "Crea un presupuesto fijo para esta categoria y adherete a el.",
    },
    "subscription_creep": {
        "headline": "Detectamos un gasto recurrente no registrado.",
        "why": (
            "Encontramos un patron de gasto de ~{amount:.0f} cada {days:.0f} dias ({count} veces)."
        ),
        "how": ("Podria ser una suscripcion que no esta registrada en el sistema."),
        "impact": (
            "Registrar esta suscripcion te permite trackear su impacto y decidir si cancelarla."
        ),
        "action": "Registra esta suscripcion en el sistema para mejor tracking.",
    },
}


class Explainer:
    """Generates personalized explanations for recommendations."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm_client = llm_client

    async def explain(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        recommendation: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a personalized explanation for a recommendation.

        Uses LLM first if available, falls back to template-based generation.
        """
        rec_type = recommendation.get("type", "")
        features = recommendation.get("features_used", {})

        # Try LLM first
        if self._llm_client is not None:
            result = await self._try_llm_explanation(session, user_id, recommendation)
            if result is not None:
                return result

        # Fallback to template-based explanation
        return await self._template_explanation(session, user_id, recommendation)

    async def _try_llm_explanation(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        recommendation: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Try to generate explanation via LLM. Returns None on failure."""
        rec_type = recommendation.get("type", "")
        features = recommendation.get("features_used", {})

        # Check cache
        cache_key = self._cache_key(user_id, rec_type, features)
        cached = _EXPLANATION_CACHE.get(cache_key)
        if cached is not None:
            elapsed = time.time() - cached[0]
            if elapsed < _CACHE_TTL_SECONDS:
                logger.debug("explanation_cache_hit", rec_type=rec_type)
                return cached[1]

        # Gather user context for the prompt
        context = await self._get_context_data(session, user_id)

        prompt = USER_PROMPT_EXPLANATION.format(
            rec_type=rec_type,
            title=recommendation.get("title", ""),
            description=recommendation.get("description", ""),
            priority=recommendation.get("priority", "medium"),
            confidence=recommendation.get("confidence", 0.5),
            estimated_savings=recommendation.get("estimated_savings", 0),
            income=context.get("income", 0),
            expense=context.get("expense", 0),
            balance=context.get("balance", 0),
            top_category=context.get("top_category", "N/A"),
            tx_count=context.get("tx_count", 0),
            months_data=context.get("months_data", 0),
        )

        raw = await self._llm_client.generate(
            prompt, system_prompt=SYSTEM_PROMPT_EXPLANATION
        )
        if raw is None:
            return None

        parsed = self._parse_llm_json(raw)
        if parsed is None:
            logger.warning("llm_response_parse_failed", rec_type=rec_type, raw=raw[:200])
            return None

        result = {
            "headline": parsed.get("headline", ""),
            "why": parsed.get("why", ""),
            "how": parsed.get("how", ""),
            "impact": parsed.get("impact", ""),
            "action": parsed.get("action", ""),
            "tone": self._determine_tone(recommendation, context),
            "personalized": True,
            "llm_generated": True,
            "rec_type": rec_type,
            "priority": recommendation.get("priority", "medium"),
            "estimated_savings": recommendation.get("estimated_savings", 0),
            "confidence": recommendation.get("confidence", 0),
        }

        # Store in cache
        _EXPLANATION_CACHE[cache_key] = (time.time(), result)
        return result

    async def _template_explanation(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        recommendation: dict[str, Any],
    ) -> dict[str, Any]:
        """Fallback: generate explanation from templates."""
        rec_type = recommendation.get("type", "")
        features = recommendation.get("features_used", {})

        template = EXPLANATION_TEMPLATES.get(rec_type)
        if not template:
            return self._fallback_explanation(recommendation)

        prefs = await self._get_user_preferences(session, user_id)
        tone = self._determine_tone(recommendation, prefs)

        return {
            "headline": template["headline"],
            "why": self._fill_template(template["why"], features),
            "how": self._fill_template(template["how"], features),
            "impact": self._fill_template(template["impact"], features),
            "action": self._fill_template(template["action"], features),
            "tone": tone,
            "personalized": True,
            "llm_generated": False,
            "rec_type": rec_type,
            "priority": recommendation.get("priority", "medium"),
            "estimated_savings": recommendation.get("estimated_savings", 0),
            "confidence": recommendation.get("confidence", 0),
        }

    async def _get_user_preferences(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Get user preferences for personalization."""
        stmt = select(UserPreferenceModel).where(UserPreferenceModel.user_id == user_id)
        result = await session.execute(stmt)
        prefs = result.scalar_one_or_none()
        if prefs:
            return {
                "language": prefs.language,
                "currency": prefs.currency_code,
            }
        return {"language": "es", "currency": "DOP"}

    async def _get_context_data(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Gather user financial context for the LLM prompt."""
        from datetime import date, timedelta

        today = date.today()
        six_months_ago = today - timedelta(days=180)
        month_start = today.replace(day=1)

        stmt = (
            select(TransactionModel)
            .where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.status == "completed",
                    TransactionModel.effective_date >= six_months_ago,
                    TransactionModel.effective_date <= today,
                )
            )
            .order_by(TransactionModel.effective_date.asc())
        )
        result = await session.execute(stmt)
        transactions = list(result.scalars().all())

        income = sum(
            float(t.amount) for t in transactions if t.transaction_type == "income"
        )
        expense = sum(
            abs(float(t.amount)) for t in transactions if t.transaction_type == "expense"
        )

        monthly_months: set[str] = set()
        category_totals: dict[str, float] = {}
        current_month_count = 0

        for t in transactions:
            monthly_months.add(t.effective_date.strftime("%Y-%m"))
            cat = t.category.name if t.category else "Otros"
            category_totals[cat] = category_totals.get(cat, 0) + abs(float(t.amount))
            if t.effective_date >= month_start:
                current_month_count += 1

        top_category = max(category_totals, key=category_totals.get) if category_totals else "N/A"

        return {
            "income": round(income, 2),
            "expense": round(expense, 2),
            "balance": round(income - expense, 2),
            "top_category": top_category,
            "tx_count": current_month_count,
            "months_data": len(monthly_months),
        }

    def _parse_llm_json(self, raw: str) -> dict[str, Any] | None:
        """Try to parse LLM response as JSON."""
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        try:
            data = json.loads(cleaned)
            required = {"headline", "why", "how", "impact", "action"}
            if required.issubset(data.keys()):
                return data
            logger.warning("llm_json_missing_keys", missing=required - data.keys())
            return None
        except json.JSONDecodeError:
            return None

    def _cache_key(
        self,
        user_id: uuid.UUID,
        rec_type: str,
        features: dict[str, Any],
    ) -> str:
        """Build a cache key from user, rec type, and features."""
        feature_hash = hash(frozenset(features.items()))
        return f"{user_id}:{rec_type}:{feature_hash}"

    def _determine_tone(
        self,
        recommendation: dict[str, Any],
        prefs: dict[str, Any],
    ) -> str:
        """Determine the tone based on recommendation severity."""
        priority = recommendation.get("priority", "medium")
        score = recommendation.get("confidence", 0)

        if priority == "high" and score > 0.8:
            return "urgent"
        if priority == "high":
            return "concerned"
        if priority == "low":
            return "informative"
        return "encouraging"

    def _fill_template(self, template: str, features: dict[str, Any]) -> str:
        """Fill a template string with feature values."""
        try:
            replacements = {}
            for key, value in features.items():
                if isinstance(value, (int, float)):
                    replacements[key] = value
                elif isinstance(value, str):
                    replacements[key] = value
                else:
                    replacements[key] = str(value)

            if "annual" not in replacements and "savings" in replacements:
                replacements["annual"] = replacements["savings"] * 12
            if "monthly" not in replacements and "gap" in replacements:
                replacements["monthly"] = replacements["gap"]
            if "annual" not in replacements and "gap" in replacements:
                replacements["annual"] = replacements["gap"] * 12

            return template.format(**replacements)
        except (KeyError, ValueError):
            return template

    def _fallback_explanation(
        self,
        recommendation: dict[str, Any],
    ) -> dict[str, Any]:
        """Fallback explanation when no template exists."""
        return {
            "headline": recommendation.get("title", "Recomendacion disponible"),
            "why": recommendation.get("description", ""),
            "how": "Basado en el analisis de tus transacciones recientes.",
            "impact": (f"Ahorro estimado: {recommendation.get('estimated_savings', 0):.0f}/mes."),
            "action": "Revisa los detalles de esta recomendacion.",
            "tone": "informative",
            "personalized": False,
            "llm_generated": False,
            "rec_type": recommendation.get("type", "unknown"),
            "priority": recommendation.get("priority", "medium"),
            "estimated_savings": recommendation.get("estimated_savings", 0),
            "confidence": recommendation.get("confidence", 0),
        }
