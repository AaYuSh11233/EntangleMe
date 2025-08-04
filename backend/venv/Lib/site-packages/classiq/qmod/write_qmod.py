import json
from pathlib import Path
from typing import Optional, Union

from classiq.interface.constants import DEFAULT_DECIMAL_PRECISION
from classiq.interface.model.model import Model, SerializedModel

from classiq.qmod.global_declarative_switch import set_global_declarative_switch
from classiq.qmod.native.pretty_printer import DSLPrettyPrinter
from classiq.qmod.quantum_function import GenerativeQFunc, QFunc

_QMOD_SUFFIX = "qmod"
_SYNTHESIS_OPTIONS_SUFFIX = "synthesis_options.json"


def write_qmod(
    model: Union[SerializedModel, QFunc, GenerativeQFunc],
    name: str,
    directory: Optional[Path] = None,
    decimal_precision: int = DEFAULT_DECIMAL_PRECISION,
    symbolic_only: bool = True,
) -> None:
    """
    Creates a native Qmod file from a serialized model and outputs the synthesis options (Preferences and Constraints) to a file.
    The native Qmod file may be uploaded to the Classiq IDE.

    Args:
        model: The entry point of the Qmod model - a qfunc named 'main' (or alternatively the output of 'create_model').
        name: The name to save the file by.
        directory: The directory to save the files in. If None, the current working directory is used.
        decimal_precision: The number of decimal places to use for numbers, set to 4 by default.
        symbolic_only: If True keep function definitions un-expanded and symbolic (note that Qmod functions with parameters of Python types are not supported in this mode)

    Returns:
        None
    """
    model_obj = prepare_write_qmod_model(model, symbolic_only)
    pretty_printed_model = DSLPrettyPrinter(decimal_precision=decimal_precision).visit(
        model_obj
    )
    synthesis_options = model_obj.model_dump(
        include={"constraints", "preferences"}, exclude_none=True
    )

    synthesis_options_path = Path(f"{name}.{_SYNTHESIS_OPTIONS_SUFFIX}")
    if directory is not None:
        synthesis_options_path = directory / synthesis_options_path

    synthesis_options_path.write_text(
        json.dumps(synthesis_options, indent=2, sort_keys=True)
    )

    native_qmod_path = Path(f"{name}.{_QMOD_SUFFIX}")
    if directory is not None:
        native_qmod_path = directory / native_qmod_path

    native_qmod_path.write_text(pretty_printed_model)


def prepare_write_qmod_model(
    model: Union[SerializedModel, QFunc, GenerativeQFunc], symbolic_only: bool
) -> Model:
    if isinstance(model, str) and hasattr(model, "entry_point") and symbolic_only:
        model_obj = Model.model_validate_json(model)
        with set_global_declarative_switch():
            dec_model_obj = model.entry_point.create_model(
                constraints=model_obj.constraints,
                execution_preferences=model_obj.execution_preferences,
                preferences=model_obj.preferences,
            )
        dec_constant_names = {const.name for const in dec_model_obj.constants}
        all_constants = dec_model_obj.constants + [
            const
            for const in model_obj.constants
            if const.name not in dec_constant_names
        ]
        return dec_model_obj.model_copy(
            update={
                "constants": all_constants,
                "classical_execution_code": model_obj.classical_execution_code,
            }
        )
    if isinstance(model, (QFunc, GenerativeQFunc)):
        if symbolic_only:
            with set_global_declarative_switch():
                return model.create_model()
        return model.create_model()
    return Model.model_validate_json(model)
