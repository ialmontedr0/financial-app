"""Tax use cases."""

from .create_category import CreateTaxCategoryUseCase
from .create_deduction import CreateTaxDeductionUseCase
from .delete_category import DeleteTaxCategoryUseCase
from .delete_deduction import DeleteTaxDeductionUseCase
from .get_deduction import GetTaxDeductionUseCase
from .get_tax_summary import GetTaxSummaryUseCase
from .list_categories import ListTaxCategoriesUseCase
from .list_deductions import ListTaxDeductionsUseCase
from .update_deduction import UpdateTaxDeductionUseCase

__all__ = [
    "CreateTaxCategoryUseCase",
    "CreateTaxDeductionUseCase",
    "DeleteTaxCategoryUseCase",
    "DeleteTaxDeductionUseCase",
    "GetTaxDeductionUseCase",
    "GetTaxSummaryUseCase",
    "ListTaxCategoriesUseCase",
    "ListTaxDeductionsUseCase",
    "UpdateTaxDeductionUseCase",
]
