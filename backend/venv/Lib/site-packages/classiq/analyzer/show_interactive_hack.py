import os
import subprocess
import webbrowser
from collections.abc import Awaitable, Callable
from tempfile import NamedTemporaryFile
from urllib.parse import urljoin

from classiq.interface.analyzer.result import DataID
from classiq.interface.exceptions import ClassiqAnalyzerVisualizationError
from classiq.interface.generator.model.preferences.preferences import QuantumFormat
from classiq.interface.generator.quantum_program import QuantumProgram

from classiq._internals.api_wrapper import ApiWrapper
from classiq._internals.async_utils import is_notebook, syncify_function
from classiq.analyzer.url_utils import circuit_page_uri, client_ide_base_url
from classiq.visualization import visualize_async

VisualizationRenderer = Callable[[DataID, QuantumProgram], Awaitable[None]]

# In Classiq Studio (openvscode env) we use this command to open files
VSCODE_COMMAND = "code"


def is_classiq_studio() -> bool:
    # Perhaps in the future we should add a dedicated unique environment var
    #  but so far should work just fine.
    return bool(os.environ.get("OPENVSCODE"))


def get_app_url(
    data_id: DataID, circuit: QuantumProgram, include_query: bool = True
) -> str:
    return urljoin(
        client_ide_base_url(),
        circuit_page_uri(
            circuit_id=data_id.id,
            circuit_version=circuit.version,
            include_query=include_query,
        ),
    )


async def ide_renderer(data_id: DataID, circuit: QuantumProgram) -> None:
    app_url = get_app_url(data_id, circuit)
    webbrowser.open_new_tab(app_url)


async def editor_renderer(data_id: DataID, circuit: QuantumProgram) -> None:
    with NamedTemporaryFile(
        delete=False, prefix=f"{data_id.id}-", suffix=".qprog", mode="w"
    ) as file:
        analyzer_data = await ApiWrapper.get_analyzer_app_data(data_id)
        file.write(analyzer_data.model_dump_json())
    subprocess.run([VSCODE_COMMAND, file.name])


async def notebook_renderer(data_id: DataID, circuit: QuantumProgram) -> None:
    from IPython.display import display  # type: ignore[import]

    visual_model = await visualize_async(data_id)
    app_url = get_app_url(data_id, circuit)
    display(
        {
            # Attempt to handle by notebook renderer from Classiq vscode extension
            "application/vnd.classiq+qviz": visual_model,
            # Fallback to IDE link display when no extension available.
            #  Shouldn't normally happen.
            #  Otherwise, is_classiq_studio detection is not correct.
            "text/plain": app_url,
        },
        raw=True,
        metadata={
            "url": app_url,
        },
    )


def get_visualization_renderer() -> VisualizationRenderer:
    # Ideally, we should check if a registered custom mime type handler is available,
    #  or at least if the Classiq vscode extension is installed.
    #  There's no such capabilities in IPython, so we make assumption from a fact that
    #  it's a Classiq Studio env.
    #  (Studio always has the extension, and the extension always supports mime type).
    if not is_classiq_studio():
        return ide_renderer
    # For non-interactive environments, write a temporary file and open it
    if not is_notebook():
        return editor_renderer
    # For interactive notebooks, visualize and render as inline content
    return notebook_renderer


async def handle_remote_app(circuit: QuantumProgram, display_url: bool = True) -> None:
    if circuit.outputs.get(QuantumFormat.QASM) is None:
        raise ClassiqAnalyzerVisualizationError(
            "Missing QASM transpilation: visualization is only supported "
            "for QASM programs. Try adding QASM to the output formats "
            "synthesis preferences"
        )
    circuit_dataid = await ApiWrapper.call_analyzer_app(circuit)

    renderer = get_visualization_renderer()
    if display_url:
        app_url = get_app_url(circuit_dataid, circuit, include_query=False)
        print(f"Quantum program link: {app_url}")  # noqa: T201
    await renderer(circuit_dataid, circuit)


async def _show_interactive(self: QuantumProgram, display_url: bool = True) -> None:
    """
    Displays the interactive representation of the quantum program in the Classiq IDE.

    Args:
        self:
            The serialized quantum program to be displayed.
        display_url:
            Whether to print the url

    Links:
        [Visualization tool](https://docs.classiq.io/latest/user-guide/analysis/quantum-program-visualization-tool/)
    """
    await handle_remote_app(self, display_url)


QuantumProgram.show = syncify_function(_show_interactive)  # type: ignore[attr-defined]
QuantumProgram.show_async = _show_interactive  # type: ignore[attr-defined]
