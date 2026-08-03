"""Insurance use cases."""

from .create_insurance import CreateInsuranceUseCase
from .create_policy import CreatePolicyUseCase
from .create_premium import CreatePremiumUseCase
from .delete_insurance import DeleteInsuranceUseCase
from .delete_policy import DeletePolicyUseCase
from .delete_premium import DeletePremiumUseCase
from .get_insurance import GetInsuranceUseCase
from .get_insurance_dashboard import GetInsuranceDashboardUseCase
from .list_insurances import ListInsurancesUseCase
from .list_policies import ListPoliciesUseCase
from .list_premiums import ListPremiumsUseCase
from .mark_premium_paid import MarkPremiumPaidUseCase
from .update_insurance import UpdateInsuranceUseCase
from .update_insurance_status import UpdateInsuranceStatusUseCase

__all__ = [
    "CreateInsuranceUseCase",
    "CreatePolicyUseCase",
    "CreatePremiumUseCase",
    "DeleteInsuranceUseCase",
    "DeletePolicyUseCase",
    "DeletePremiumUseCase",
    "GetInsuranceDashboardUseCase",
    "GetInsuranceUseCase",
    "ListInsurancesUseCase",
    "ListPoliciesUseCase",
    "ListPremiumsUseCase",
    "MarkPremiumPaidUseCase",
    "UpdateInsuranceStatusUseCase",
    "UpdateInsuranceUseCase",
]
