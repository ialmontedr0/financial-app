"""Use case: List supported ISO 4217 currencies."""

from __future__ import annotations

from app.domain.users.value_objects import SUPPORTED_CURRENCIES


class GetSupportedCurrenciesUseCase:
    """Return the currencies the platform supports, with human labels."""

    async def execute(self) -> list[dict[str, str]]:
        """Return the supported currencies as code/label pairs."""
        return [{"code": code, "name": name} for code, name in sorted(SUPPORTED_CURRENCIES.items())]
