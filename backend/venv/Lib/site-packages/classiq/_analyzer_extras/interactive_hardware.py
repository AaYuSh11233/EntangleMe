import json
from typing import Optional

import plotly.graph_objects as go
from ipywidgets import Combobox, HBox, VBox  # type: ignore[import]

from classiq.interface.analyzer import analysis_params
from classiq.interface.backend.quantum_backend_providers import AnalyzerProviderVendor
from classiq.interface.generator.quantum_program import QuantumProgram

from classiq._analyzer_extras._ipywidgets_async_extension import widget_callback
from classiq.analyzer.analyzer_utilities import (
    AnalyzerUtilities,
    DeviceName,
    HardwareGraphs,
    ProviderAvailableDevices,
    ProviderNameEnum,
)


class InteractiveHardware(AnalyzerUtilities):
    def __init__(
        self,
        params: analysis_params.AnalysisParams,
        circuit: QuantumProgram,
        available_devices: ProviderAvailableDevices,
        hardware_graphs: HardwareGraphs,
    ) -> None:
        super().__init__(params, circuit, available_devices, hardware_graphs)
        self.providers_combobox = self._initialize_providers_combobox()
        self.devices_combobox = self._initialize_devices_combobox()
        self.hardware_graph = self._initialize_hardware_graph()

    def show_interactive_graph(self) -> VBox:
        combobox_layout = HBox([self.providers_combobox, self.devices_combobox])
        return VBox([combobox_layout, self.hardware_graph])

    async def enable_interactivity_async(self) -> None:
        await self._provider_selection_response_async()
        await self._device_selection_response_async()

    @staticmethod
    def _initialize_providers_combobox() -> Combobox:
        combobox = Combobox(
            placeholder="Choose provider",
            options=list(AnalyzerProviderVendor),
            description="providers:",
            ensure_option=True,
            disabled=False,
        )
        return combobox

    @staticmethod
    def _initialize_devices_combobox() -> Combobox:
        combobox = Combobox(
            placeholder="Choose first provider",
            description="devices:",
            ensure_option=True,
            disabled=True,
        )
        return combobox

    @staticmethod
    def _initialize_hardware_graph() -> go.FigureWidget:
        return go.FigureWidget()

    @widget_callback(widget_name="providers_combobox")
    async def _provider_selection_response_async(
        self, provider: Optional[ProviderNameEnum]
    ) -> None:
        if not provider:
            return
        await self._request_available_devices_async(providers=[provider])
        self.devices_combobox.options = self._filter_devices_by_qubits_count(provider)
        self.devices_combobox.disabled = False
        self.devices_combobox.placeholder = "Choose device"

    @widget_callback(widget_name="devices_combobox")
    async def _device_selection_response_async(
        self, device: Optional[DeviceName]
    ) -> None:
        provider = self.providers_combobox.value
        if not device or not provider:
            return
        await self.request_hardware_connectivity_async(
            provider=provider,
            device=device,
        )
        self.hardware_graph.data = []
        self.hardware_graph.update(
            dict1=json.loads(self.hardware_graphs[device]), overwrite=True
        )
