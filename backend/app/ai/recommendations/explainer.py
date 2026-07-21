"""Personalized explainer — generates natural language explanations."""

from __future__ import annotations
from sqlalchemy import select as _sel  # noqa: E402

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.user_preference import UserPreferenceModel

logger = structlog.get_logger()

# Spanish language templates
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

    async def explain(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        recommendation: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a personalized explanation for a recommendation.

        Returns:
        - headline: main takeaway
        - why: why this matters
        - how: how it happened
        - impact: potential impact
        - action: specific action to take
        - tone: encouraging/urgent/informative
        - personalized: whether personalization was applied
        """
        rec_type = recommendation.get("type", "")
        features = recommendation.get("features_used", {})

        template = EXPLANATION_TEMPLATES.get(rec_type)
        if not template:
            return self._fallback_explanation(recommendation)

        # Get user preferences for personalization
        prefs = await self._get_user_preferences(session, user_id)
        tone = self._determine_tone(recommendation, prefs)

        # Fill templates with actual values
        why = self._fill_template(template["why"], features)
        how = self._fill_template(template["how"], features)
        impact = self._fill_template(template["impact"], features)
        action = self._fill_template(template["action"], features)

        return {
            "headline": template["headline"],
            "why": why,
            "how": how,
            "impact": impact,
            "action": action,
            "tone": tone,
            "personalized": True,
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
        stmt = _sel(UserPreferenceModel).where(UserPreferenceModel.user_id == user_id)
        from sqlalchemy import select as sel

        result = await session.execute(
            sel(UserPreferenceModel).where(UserPreferenceModel.user_id == user_id)
        )
        prefs = result.scalar_one_or_none()

        if prefs:
            return {
                "language": prefs.language,
                "currency": prefs.currency_code,
            }
        return {"language": "es", "currency": "DOP"}

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
            # Map common feature keys to template placeholders
            replacements = {}
            for key, value in features.items():
                if isinstance(value, (int, float)):
                    replacements[key] = value
                elif isinstance(value, str):
                    replacements[key] = value
                else:
                    replacements[key] = str(value)

            # Add computed values if missing
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
            "rec_type": recommendation.get("type", "unknown"),
            "priority": recommendation.get("priority", "medium"),
            "estimated_savings": recommendation.get("estimated_savings", 0),
            "confidence": recommendation.get("confidence", 0),
        }


# Need this import at module level
