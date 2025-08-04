from typing import Callable

import numpy as np

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.executor.result import ParsedCounts, ParsedState


def estimate_cost(
    cost_func: Callable[[ParsedState], float],
    parsed_counts: ParsedCounts,
    quantile: float = 1.0,
) -> float:
    if quantile < 0 or quantile > 1:
        raise ClassiqValueError("'quantile' must be between 0 and 1")
    costs = np.fromiter((cost_func(sample.state) for sample in parsed_counts), float)
    shots = np.fromiter((sample.shots for sample in parsed_counts), int)

    if quantile == 1:
        return float(np.average(costs, weights=shots))
    return float(estimate_quantile_cost(costs, shots, quantile=quantile))


def estimate_quantile_cost(
    costs: np.ndarray,
    shots: np.ndarray,
    quantile: float,
) -> np.floating:
    repeated_costs = np.repeat(costs, shots)
    sort_idx = repeated_costs.argsort()
    cutoff_idx = sort_idx[: int(quantile * len(repeated_costs))]
    sorted_costs = repeated_costs[cutoff_idx]
    if sorted_costs.size == 0:
        sorted_costs = repeated_costs[sort_idx[0]]
    return np.average(sorted_costs)
