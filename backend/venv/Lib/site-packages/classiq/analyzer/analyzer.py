"""Analyzer module, implementing facilities for analyzing circuits using Classiq platform."""

import json
import webbrowser
from collections.abc import Sequence
from importlib.util import find_spec
from typing import Any, Optional, Union

import plotly.graph_objects as go

from classiq.interface.analyzer import analysis_params
from classiq.interface.backend.quantum_backend_providers import AnalyzerProviderVendor
from classiq.interface.exceptions import ClassiqAnalyzerError
from classiq.interface.generator import quantum_program as generator_result

from classiq._internals import async_utils, client
from classiq._internals.api_wrapper import ApiWrapper
from classiq.analyzer.analyzer_utilities import (
    AnalyzerUtilities,
    DeviceName,
    ProviderNameEnum,
)

find_ipywidgets = find_spec("ipywidgets")
VBox = Any

if find_ipywidgets is not None:
    from ipywidgets import VBox  # type: ignore[import, no-redef]

    from classiq._analyzer_extras.interactive_hardware import InteractiveHardware


class Analyzer(AnalyzerUtilities):
    """Analyzer is the wrapper object for all analysis capabilities."""

    def __init__(self, circuit: generator_result.QuantumProgram) -> None:
        """Init self.

        Args:
            circuit: The circuit to be analyzed.
        """
        if circuit.qasm is None:
            raise ClassiqAnalyzerError(
                "Analysis requires a circuit with valid QASM code"
            )
        params: analysis_params.AnalysisParams = analysis_params.AnalysisParams(
            qasm=circuit.qasm
        )
        super().__init__(
            params=params,
            circuit=circuit,
            available_devices=dict(),
            hardware_graphs=dict(),
        )

        self.hardware_comparison_table: Optional[go.Figure] = None

        self.transpilation_params = analysis_params.AnalysisHardwareTranspilationParams(
            hardware_data=self.circuit.hardware_data,
            random_seed=self.circuit.model.execution_preferences.random_seed,
            transpilation_option=self.circuit.model.execution_preferences.transpile_to_hardware,
        )

    def get_available_devices(
        self, providers: Optional[list[ProviderNameEnum]] = None
    ) -> dict[ProviderNameEnum, list[DeviceName]]:
        """Deprecated. Use get_all_hardware_devices instead.

        Returns dict of the available devices by the providers. only devices
        with sufficient number of qubits are returns

        Args: providers: List of providers.
        if None, the table include all the available hardware.

        Returns:
            available devices: dict of the available devices.
        """
        if providers is None:
            providers = list(AnalyzerProviderVendor)
        async_utils.run(self._request_available_devices_async(providers=providers))
        return {
            provider: self._filter_devices_by_qubits_count(provider)
            for provider in providers
        }

    def plot_hardware_connectivity(
        self,
        provider: Optional[ProviderNameEnum] = None,
        device: Optional[DeviceName] = None,
    ) -> VBox:
        """plot the hardware_connectivity graph. It is required to required  install the
        analyzer_sdk extra.

        Args:
            provider: provider name.
            device: device name.
        Returns:
         hardware_connectivity_graph: interactive graph.
        """

        self._validate_analyzer_extra()
        interactive_hardware = InteractiveHardware(
            circuit=self.circuit,
            params=self._params,
            available_devices=self.available_devices,
            hardware_graphs=self.hardware_graphs,
        )
        async_utils.run(interactive_hardware.enable_interactivity_async())
        if provider is not None:
            interactive_hardware.providers_combobox.value = provider
            if device is not None:
                interactive_hardware.devices_combobox.value = device

        return interactive_hardware.show_interactive_graph()

    def get_hardware_comparison_table(
        self,
        providers: Optional[Sequence[Union[str, AnalyzerProviderVendor]]] = None,
        devices: Optional[list[str]] = None,
    ) -> None:
        """create a comparison table between the transpiled circuits result on different hardware.
        The  comparison table included the depth, multi qubit gates count,and total gates count of the circuits.

        Args:
            providers: List of providers. if None, the table include all the available hardware.
            devices: List of devices. if None, the table include all the available devices of the selected
        providers.

        Returns:
            None.
        """
        if providers is None:
            providers = list(AnalyzerProviderVendor)
        params = analysis_params.AnalysisHardwareListParams(
            qasm=self._params.qasm,
            providers=providers,
            devices=devices,
            transpilation_params=self.transpilation_params,
        )
        result = async_utils.run(ApiWrapper.call_table_graphs_task(params=params))
        self.hardware_comparison_table = go.Figure(json.loads(result.details))

    def plot_hardware_comparison_table(
        self,
        providers: Optional[list[Union[str, AnalyzerProviderVendor]]] = None,
        devices: Optional[list[str]] = None,
    ) -> None:
        """plot the comparison table. if it has not been created it, it first creates the table using all the
        available hardware.

        Returns:
            None.
        """
        self._hardware_comparison_condition(providers=providers, devices=devices)
        self.hardware_comparison_table.show()  # type: ignore[union-attr]

    def _hardware_comparison_condition(
        self,
        providers: Optional[Sequence[Union[str, AnalyzerProviderVendor]]] = None,
        devices: Optional[list[str]] = None,
    ) -> None:
        if (
            providers is not None
            or devices is not None
            or self.hardware_comparison_table is None
        ):
            self.get_hardware_comparison_table(providers=providers, devices=devices)

    @staticmethod
    def _open_route(path: str) -> None:
        backend_uri = client.client().get_backend_uri()
        webbrowser.open_new_tab(f"{backend_uri}{path}")

    @staticmethod
    def _validate_analyzer_extra() -> None:
        if find_ipywidgets is None:
            raise ClassiqAnalyzerError(
                "To use this method, please install the `analyzer sdk`. Run the  \
                following line: - pip install classiq[analyzer_sdk]"
            )
