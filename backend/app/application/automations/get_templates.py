"""Use case: Get available automation templates."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class GetTemplatesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID) -> dict:
        return {
            "triggers": [
                {
                    "type": "income_received",
                    "name": "Ingreso recibido",
                    "description": "Se activa cuando se crea una transaccion de ingreso",
                    "params": {
                        "min_amount": "float (optional)",
                        "category_id": "UUID (optional)",
                    },
                },
                {
                    "type": "balance_threshold",
                    "name": "Umbral de saldo",
                    "description": "Se activa cuando un saldo cruza un umbral",
                    "params": {
                        "account_id": "UUID",
                        "threshold": "float",
                        "direction": "above|below",
                    },
                },
                {
                    "type": "date_scheduled",
                    "name": "Fecha programada",
                    "description": "Se activa en una fecha especifica del mes",
                    "params": {
                        "day_of_month": "int (1-28)",
                        "months": "list of ints (1-12)",
                    },
                },
                {
                    "type": "bill_due_soon",
                    "name": "Factura proxima a vencer",
                    "description": "Se activa cuando una factura esta proxima a vencer",
                    "params": {
                        "card_id": "UUID",
                        "days_before_due": "int",
                    },
                },
                {
                    "type": "budget_exceeded",
                    "name": "Presupuesto excedido",
                    "description": "Se activa cuando un presupuesto supera un umbral",
                    "params": {
                        "budget_id": "UUID",
                        "threshold_pct": "int (0-100)",
                    },
                },
                {
                    "type": "goal_completed",
                    "name": "Meta completada",
                    "description": "Se activa cuando una meta financiera se alcanza",
                    "params": {"goal_id": "UUID"},
                },
            ],
            "actions": [
                {
                    "type": "transfer",
                    "name": "Transferencia",
                    "description": "Mover dinero entre cuentas",
                    "params": {
                        "source_account_id": "UUID",
                        "target_account_id": "UUID",
                        "amount": "float",
                        "amount_type": "fixed|percent_of_balance|percent_of_surplus",
                    },
                },
                {
                    "type": "pay_credit_card",
                    "name": "Pago de tarjeta",
                    "description": "Pagar factura de tarjeta de credito",
                    "params": {
                        "card_id": "UUID",
                        "payment_account_id": "UUID",
                        "payment_type": "minimum|full|custom",
                        "custom_amount": "float (optional)",
                    },
                },
                {
                    "type": "create_transaction",
                    "name": "Crear transaccion",
                    "description": "Crear una transaccion automatica",
                    "params": {
                        "account_id": "UUID",
                        "category_id": "UUID (optional)",
                        "amount": "float",
                        "description": "string",
                        "transaction_type": "expense|income",
                    },
                },
                {
                    "type": "adjust_budget",
                    "name": "Ajustar presupuesto",
                    "description": "Ajustar automaticamente un presupuesto",
                    "params": {
                        "budget_id": "UUID",
                        "adjustment_type": "set|increase|decrease|percentage",
                        "target_amount": "float",
                    },
                },
            ],
        }
