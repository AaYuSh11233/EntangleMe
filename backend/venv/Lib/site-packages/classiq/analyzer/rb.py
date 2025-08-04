from enum import Enum as PythonEnum
from typing import Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from classiq.interface.analyzer.analysis_params import AnalysisRBParams
from classiq.interface.analyzer.result import RbResults
from classiq.interface.exceptions import ClassiqAnalyzerError

from classiq._internals.api_wrapper import ApiWrapper
from classiq.executor import BackendPreferencesAndResult


class RBAnalysis:
    def __init__(self, experiments_data: list[AnalysisRBParams]) -> None:
        """Init self.

        Args:
            experiments_data: List of results from varius RB experiments.
        """

        self.experiments_data = experiments_data
        self._total_results: pd.DataFrame = pd.DataFrame()

    async def _get_multiple_hardware_results_async(self) -> dict[str, RbResults]:
        total_result: dict[str, RbResults] = {}
        for batch in self.experiments_data:
            if len(batch.num_clifford) < 5:
                raise ClassiqAnalyzerError(
                    f"An experiment mush contain at least five sequences,"
                    f" this sequence is {len(batch.num_clifford)}"
                )
            rb_result = await ApiWrapper.call_rb_analysis_task(batch)
            total_result[batch.hardware] = rb_result
        return total_result

    @staticmethod
    def _get_df_indices(results: dict[str, RbResults]) -> list[str]:
        temp_res = results.copy()
        _, rb_result_keys = temp_res.popitem()
        return list(rb_result_keys.__dict__.keys())

    async def show_multiple_hardware_data_async(self) -> pd.DataFrame:
        """Run the RB analysis.

        Returns:
            The RB result.
        """
        results = await self._get_multiple_hardware_results_async()
        indices = RBAnalysis._get_df_indices(results)
        result_df = pd.DataFrame(index=indices)
        for hardware, result in results.items():
            result_df[hardware] = result.__dict__.values()
        self._total_results = result_df
        return result_df

    def plot_multiple_hardware_results(self) -> go.Figure:
        """Plot Bar graph of the results.

        Returns:
            None.
        """
        df = self._total_results.loc[["mean_fidelity", "average_error"]].transpose()
        hardware = list(df.index)
        params = list(df.columns)
        data = [
            go.Bar(name=param, x=hardware, y=df[param].values * 100) for param in params
        ]
        fig = go.Figure(data).update_layout(
            title="RB hardware comparison",
            barmode="group",
            yaxis=dict(title="Fidelity in %"),
            xaxis=dict(title="Hardware"),
        )
        return fig


def _strict_string(arg: Union[PythonEnum, str]) -> str:
    if isinstance(arg, PythonEnum):
        return arg.value
    return arg


def order_executor_data_by_hardware(
    mixed_data: list[BackendPreferencesAndResult],
) -> list[AnalysisRBParams]:
    hardware_names: set[str] = {
        _strict_string(hardware.backend_name) for hardware, _, _ in mixed_data
    }
    counts_dicts: dict[str, list[dict[str, int]]] = {
        name: list() for name in hardware_names
    }
    cliffords_dicts: dict[str, list[int]] = {name: list() for name in hardware_names}
    for hardware, num_clifford, result in mixed_data:
        hw_name: str = _strict_string(hardware.backend_name)
        counts_dicts[hw_name].append(result.counts)  # type: ignore[union-attr]
        cliffords_dicts[hw_name].append(num_clifford)

    return [
        AnalysisRBParams(
            hardware=hw_name,
            counts=counts_dicts[hw_name],
            num_clifford=cliffords_dicts[hw_name],
        )
        for hw_name in hardware_names
    ]


def fit_to_exponential_function(
    result: RbResults, num_clifford: list[int], ax: Optional[plt.Axes] = None
) -> None:
    if ax is None:
        plt.figure()
        ax = plt.gca()

    x = np.array(num_clifford)
    ax.plot(
        x,
        np.array(result.success_probability),
        color="blue",
        linestyle="none",
        marker="o",
    )

    def fit_function(m: np.array, a: float, mean_fidelity: float, b: float) -> np.array:  # type: ignore[valid-type]
        return a * (mean_fidelity**m) + b

    ax.plot(
        x,
        fit_function(m=x, a=result.A, mean_fidelity=result.mean_fidelity, b=result.B),
        color="gray",
        linestyle="-",
        linewidth=0.5,
    )

    ax.set_xlabel("Number of Clifford gates used", fontsize=10)
    ax.set_ylabel("Success probability", fontsize=10)
    ax.text(
        0.6,
        0.9,
        f"Mean fidelity: {result.mean_fidelity} Avg. error: {result.average_error}",
        ha="center",
        va="center",
        size=10,
        bbox=dict(boxstyle="round, pad=0.3", fc="white", ec="black", lw=0.5),
        transform=ax.transAxes,
    )

    plt.show()
