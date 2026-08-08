"""Lent loan API schemas (préstamo otorgado)."""

from __future__ import annotations

import calendar
import re
from datetime import date

from pydantic import BaseModel, Field, model_validator

_MONTH_YEAR_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
PAYMENT_FREQUENCIES = ("monthly", "bi_weekly", "weekly", "single_payment")


def _validate_single_payment_date(
    payment_frequency: str, single_payment_date: str | None
) -> None:
    if payment_frequency == "single_payment":
        if not single_payment_date:
            raise ValueError(
                "single_payment_date es requerida para la frecuencia 'single_payment'"
            )
        if not _MONTH_YEAR_RE.match(single_payment_date):
            raise ValueError("single_payment_date debe tener formato YYYY-MM")
    elif single_payment_date:
        raise ValueError(
            "single_payment_date solo aplica a la frecuencia 'single_payment'"
        )


def _last_day_of_month(value: str) -> date:
    year, month = int(value[:4]), int(value[5:7])
    return date(year, month, calendar.monthrange(year, month)[1])


class SimulateLentLoanSchema(BaseModel):
    principal_amount: float = Field(..., gt=0)
    annual_interest_rate: float = Field(..., ge=0)
    term_months: int | None = Field(None, gt=0, le=600)
    payment_frequency: str = Field("monthly", pattern=r"^(monthly|bi_weekly|weekly|single_payment)$")
    start_date: str | None = None
    single_payment_date: str | None = None

    @model_validator(mode="after")
    def validate_frequency(self) -> SimulateLentLoanSchema:
        _validate_single_payment_date(self.payment_frequency, self.single_payment_date)
        if self.payment_frequency == "single_payment":
            self.single_payment_date = _last_day_of_month(
                self.single_payment_date  # type: ignore[arg-type]
            ).isoformat()
        return self


class CreateLentLoanSchema(BaseModel):
    borrower_name: str = Field(..., min_length=1, max_length=200)
    principal_amount: float = Field(..., gt=0)
    annual_interest_rate: float = Field(..., ge=0)
    term_months: int | None = Field(None, gt=0, le=600)
    payment_frequency: str = Field("monthly", pattern=r"^(monthly|bi_weekly|weekly|single_payment)$")
    currency_code: str = Field("DOP", min_length=3, max_length=3)
    account_id: str | None = None
    start_date: str | None = None
    is_collateralized: bool = False
    notes: str | None = Field(None, max_length=1000)
    single_payment_date: str | None = None

    @model_validator(mode="after")
    def validate_frequency(self) -> CreateLentLoanSchema:
        _validate_single_payment_date(self.payment_frequency, self.single_payment_date)
        if self.payment_frequency == "single_payment":
            self.single_payment_date = _last_day_of_month(
                self.single_payment_date  # type: ignore[arg-type]
            ).isoformat()
        return self


class RecordLentLoanPaymentSchema(BaseModel):
    amount: float = Field(..., gt=0)
    received_date: str | None = None
    payment_method: str = Field(
        "bank_transfer",
        pattern=r"^(bank_transfer|cash|auto_debit|check|online|mobile)$",
    )
    reference_number: str | None = Field(None, max_length=100)
    notes: str | None = Field(None, max_length=1000)
