import more_itertools
import numpy as np
import pydantic
from pydantic import BaseModel

from classiq.interface.exceptions import ClassiqValueError

_TOLERANCE_DECIMALS = 6


class PlotData(BaseModel):
    # We are currently ignoring units. This might need to be handled in the future
    x: float = pydantic.Field(description="The X coordinate of this plot")
    y: float = pydantic.Field(description="The Y coordinate of this plot")
    t: float = pydantic.Field(description="The time stamp of this plot")
    plot_id: pydantic.NonNegativeInt = pydantic.Field(
        description="The plot ID of this plot"
    )


class MhtQaoaInput(BaseModel):
    reps: pydantic.PositiveInt = pydantic.Field(
        default=3, description="Number of QAOA layers."
    )
    plot_list: list[PlotData] = pydantic.Field(
        description="The list of (x,y,t) plots of the MHT problem."
    )
    misdetection_maximum_time_steps: pydantic.NonNegativeInt = pydantic.Field(
        default=0,
        description="The maximum number of time steps a target might be misdetected.",
    )
    penalty_energy: float = pydantic.Field(
        default=2,
        description="Penalty energy for invalid solutions. The value affects "
        "the converges rate. Small positive values are preferred",
    )
    three_local_coeff: float = pydantic.Field(
        default=0,
        description="Coefficient for the 3-local terms in the Hamiltonian. It is related to the angular acceleration.",
    )
    one_local_coeff: float = pydantic.Field(
        default=0, description="Coefficient for the 1-local terms in the Hamiltonian."
    )
    is_penalty: bool = pydantic.Field(
        default=True, description="Build Pubo using penalty terms"
    )
    max_velocity: float = pydantic.Field(
        default=0, description="Max allowed velocity for a segment"
    )

    def is_valid_cost(self, cost: float) -> bool:
        return True

    @pydantic.field_validator("plot_list")
    @classmethod
    def round_plot_list_times_and_validate(
        cls, plot_list: list[PlotData]
    ) -> list[PlotData]:
        MhtQaoaInput._check_all_ids_are_distinct(plot_list)
        MhtQaoaInput._round_to_tolerance_decimals(plot_list)

        time_stamps = sorted({plot.t for plot in plot_list})
        time_diff_set = {
            np.round(time_stamps[i] - time_stamps[i - 1], decimals=_TOLERANCE_DECIMALS)
            for i in range(1, len(time_stamps))
        }

        if len(time_diff_set) != 1:
            raise ClassiqValueError(
                "The time difference between each time stamp is not equal"
            )

        return plot_list

    @staticmethod
    def _round_to_tolerance_decimals(plot_list: list[PlotData]) -> None:
        for plot in plot_list:
            plot.t = np.round(plot.t, decimals=_TOLERANCE_DECIMALS)

    @staticmethod
    def _check_all_ids_are_distinct(plot_list: list[PlotData]) -> None:
        if not more_itertools.all_unique(plot.plot_id for plot in plot_list):
            raise ClassiqValueError("Plot IDs should be unique.")
