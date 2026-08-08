"""Serialize LentLoan objects for the APIs (lender perspective)."""

from __future__ import annotations

from app.infrastructure.models.lent_loan import LentLoanModel, LentLoanPaymentModel


def serialize_payment(payment: LentLoanPaymentModel) -> dict:
    return {
        "id": str(payment.id),
        "amount": float(payment.amount),
        "principal_portion": float(payment.principal_portion),
        "interest_portion": float(payment.interest_portion),
        "received_date": payment.received_date.isoformat() if payment.received_date else None,
        "payment_method": payment.payment_method,
        "reference_number": payment.reference_number,
        "notes": payment.notes,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
    }


def serialize_lent_loan(
    loan: LentLoanModel, payments: list[LentLoanPaymentModel] | None = None, schedule: list | None = None,
) -> dict:
    """JSON-friendly representation of a lent loan."""
    base = {
        "id": str(loan.id),
        "borrower_name": loan.borrower_name,
        "notes": loan.notes,
        "principal_amount": float(loan.principal_amount),
        "annual_interest_rate": float(loan.annual_interest_rate),
        "term_months": loan.term_months,
        "payment_frequency": loan.payment_frequency,
        "currency_code": loan.currency_code,
        "monthly_payment": float(loan.monthly_payment),
        "current_balance": float(loan.current_balance),
        "total_received": float(loan.total_received),
        "total_interest_expected": float(loan.total_interest_expected),
        "total_interest_received": float(loan.total_interest_received),
        "is_collateralized": loan.is_collateralized,
        "start_date": loan.start_date.isoformat() if loan.start_date else None,
        "first_payment_date": loan.first_payment_date.isoformat()
        if loan.first_payment_date
        else None,
        "next_payment_date": loan.next_payment_date.isoformat()
        if loan.next_payment_date
        else None,
        "final_payment_date": loan.final_payment_date.isoformat()
        if loan.final_payment_date
        else None,
        "paid_off_date": loan.paid_off_date.isoformat() if loan.paid_off_date else None,
        "single_payment_date": loan.single_payment_date.isoformat()
        if loan.single_payment_date
        else None,
        "status": loan.status,
        "progress_pct": (
            round(
                (float(loan.principal_amount) - float(loan.current_balance))
                / float(loan.principal_amount)
                * 100,
                2,
            )
            if loan.principal_amount > 0
            else 0
        ),
        "account_id": str(loan.account_id) if loan.account_id else None,
        "created_at": loan.created_at.isoformat() if loan.created_at else None,
        "updated_at": loan.updated_at.isoformat() if loan.updated_at else None,
    }
    if payments is not None:
        base["payments"] = [serialize_payment(p) for p in payments]
    if schedule is not None:
        base["schedule"] = schedule
    return base
