from typing import Optional

from classiq.interface.backend.quantum_backend_providers import ProviderVendor
from classiq.interface.executor.user_budget import UserBudgets

from classiq._internals.api_wrapper import ApiWrapper
from classiq._internals.async_utils import syncify_function

PROVIDER_MAPPER = {
    ProviderVendor.IONQ: "IONQ",
    ProviderVendor.IBM_QUANTUM: "IBM_CLOUD",
    ProviderVendor.AZURE_QUANTUM: "AZURE",
    ProviderVendor.AMAZON_BRAKET: "AMAZON",
    ProviderVendor.GOOGLE: "GOOGLE",
    ProviderVendor.ALICE_AND_BOB: "ALICE_AND_BOB",
    ProviderVendor.OQC: "OQC",
    ProviderVendor.INTEL: "INTEL",
    ProviderVendor.AQT: "AQT",
    ProviderVendor.IQCC: "IQCC",
    ProviderVendor.CLASSIQ: "CLASSIQ",
}


async def get_budget_async(
    provider_vendor: Optional[ProviderVendor] = None,
) -> UserBudgets:

    budgets_list = await ApiWrapper().call_get_all_budgets()
    if provider_vendor:
        provider = PROVIDER_MAPPER.get(provider_vendor, None)
        budgets_list = [
            budget for budget in budgets_list if budget.provider == provider
        ]

    return UserBudgets(budgets=budgets_list)


get_budget = syncify_function(get_budget_async)


async def set_budget_limit_async(
    provider_vendor: ProviderVendor,
    limit: float,
) -> UserBudgets:
    provider = PROVIDER_MAPPER.get(provider_vendor, None)
    if not provider:
        raise ValueError(f"Unsupported provider: {provider_vendor}")

    budget = get_budget(provider_vendor)
    if budget is None:
        raise ValueError(f"No budget found for provider: {provider_vendor}")

    if limit <= 0:
        raise ValueError("Budget limit must be greater than zero.")

    if limit > budget.budgets[0].available_budget:
        print(  # noqa: T201
            f"Budget limit {limit} exceeds available budget {budget.budgets[0].available_budget} for provider {provider_vendor}.\n"
            "Setting budget limit to the maximum available budget."
        )
    budgets_list = await ApiWrapper().call_set_budget_limit(provider, limit)
    return UserBudgets(budgets=[budgets_list])


set_budget_limit = syncify_function(set_budget_limit_async)


async def clear_budget_limit_async(provider_vendor: ProviderVendor) -> UserBudgets:
    provider = PROVIDER_MAPPER.get(provider_vendor, None)
    if not provider:
        raise ValueError(f"Unsupported provider: {provider_vendor}")

    budgets_list = await ApiWrapper().call_clear_budget_limit(provider)
    return UserBudgets(budgets=[budgets_list])


clear_budget_limit = syncify_function(clear_budget_limit_async)
