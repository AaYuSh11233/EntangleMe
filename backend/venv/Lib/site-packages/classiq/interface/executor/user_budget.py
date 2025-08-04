import datetime
from typing import Optional

import pydantic
from pydantic import ConfigDict, Field
from tabulate import tabulate

from classiq.interface.helpers.versioned_model import VersionedModel


class UserBudget(VersionedModel):
    provider: str
    currency_code: str
    organization: Optional[str] = Field(default=None)
    available_budget: float
    used_budget: float
    last_allocation_date: datetime.datetime
    budget_limit: Optional[float] = Field(default=None)

    model_config = ConfigDict(extra="ignore")


class UserBudgets(VersionedModel):
    budgets: list[UserBudget] = pydantic.Field(default=[])

    def __str__(self) -> str:
        rows = [
            [
                budget.provider,
                f"{budget.used_budget:.3f}",
                f"{budget.available_budget:.3f}",
                (
                    f"{budget.budget_limit:.3f}"
                    if budget.budget_limit is not None
                    else "NOT SET"
                ),
                budget.currency_code,
            ]
            for budget in self.budgets
        ]

        headers = [
            "Provider",
            "Used Budget",
            "Remaining Budget",
            "Budget Limit",
            "Currency",
        ]
        return tabulate(rows, headers=headers, tablefmt="grid")
