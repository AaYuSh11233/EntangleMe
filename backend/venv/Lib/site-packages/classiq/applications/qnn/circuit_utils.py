import itertools
from collections.abc import Collection, Iterable
from typing import Union

from torch import Tensor

from classiq.interface.exceptions import ClassiqQNNError, ClassiqValueError
from classiq.interface.generator.circuit_code.types_and_constants import QasmVersion
from classiq.interface.generator.model.preferences.preferences import QuantumFormat
from classiq.interface.generator.quantum_program import QuantumProgram

from classiq.applications.qnn.types import Arguments, Circuit

WEIGHT_INITIALS = ["weight_", "w_"]
INPUT_INITIALS = ["input_", "i_"]

Parameters = list[str]
ParametersTuple = tuple[Parameters, Parameters]


def _is_name_valid(name: str) -> bool:
    return any(name.startswith(i) for i in (*WEIGHT_INITIALS, *INPUT_INITIALS))


def validate_circuit(circuit: Circuit) -> bool:
    # validate output type - QASM3
    if not (
        (QuantumFormat.QASM in circuit.outputs)
        and (circuit.qasm)
        and (circuit.qasm_version == QasmVersion.V3)
    ):
        raise ClassiqQNNError(
            "Invalid `GeneratedCircuit` object - please make sure the output format is `QASM` version 3"
        )

    # validate parameters
    if circuit.data is None:
        raise ClassiqQNNError("Invalid `GeneratedCircuit` metrics object")

    all_parameters = circuit.data.circuit_parameters
    if not (all_parameters and all(map(_is_name_valid, all_parameters))):
        raise ClassiqQNNError(
            f"Invalid parameters. please make sure all parameters start with one of the following initials: {[*WEIGHT_INITIALS, *INPUT_INITIALS]}"
        )

    return True


def _extract_by_prefix(lst: Parameters, prefix: list[str]) -> Parameters:
    return [s for s in lst if any(s.startswith(p) for p in prefix)]


def extract_parameters(circuit: Circuit) -> ParametersTuple:
    if circuit.data is None:
        raise ClassiqQNNError(
            "Invalid `GeneratedCircuit` metrics object. Please try to synthesize the circuit again."
        )

    all_parameters = circuit.data.circuit_parameters
    weights = _extract_by_prefix(all_parameters, WEIGHT_INITIALS)
    inputs = _extract_by_prefix(all_parameters, INPUT_INITIALS)
    return weights, inputs


_number_types = (int, float)
_single_item_shape = Tensor([1])[0].shape


def _validate_tensor(t: Tensor, expected_length: int, tensor_name: str) -> None:
    if not isinstance(t, Collection):
        raise ClassiqValueError(
            f'Invalid {tensor_name} type. "Tensor" expected. Got {t.__class__.__name__}'
        )

    for item in t:
        if (
            (not isinstance(item, Tensor))
            or (item.shape != _single_item_shape)
            or (not isinstance(item.item(), _number_types))
        ):
            raise ClassiqValueError(
                f'Invalid {tensor_name} type. "Tensor" of "float" expected. Got {item.__class__.__name__}'
            )

    if len(t) != expected_length:
        raise ClassiqValueError(
            f"Length mismatch. {len(t)} items given, were only {expected_length} are expected"
        )


CircuitOrExtractedParameters = Union[Circuit, ParametersTuple]


def _get_extracted_parameters(obj: CircuitOrExtractedParameters) -> ParametersTuple:
    # This `if` is for caching
    if isinstance(obj, tuple):
        weight_params, input_params = obj
    elif isinstance(obj, QuantumProgram):
        weight_params, input_params = extract_parameters(obj)
    else:
        raise ClassiqValueError("Invalid object passed to `map_parameters`")
    return weight_params, input_params


def map_parameters(
    obj: CircuitOrExtractedParameters, inputs: Tensor, weights: Tensor
) -> Arguments:
    weight_params, input_params = _get_extracted_parameters(obj)

    _validate_tensor(inputs, len(input_params), "inputs")
    _validate_tensor(weights, len(weight_params), "weights")

    return {
        **dict(zip(input_params, inputs.tolist())),
        **dict(zip(weight_params, weights.tolist())),
    }


def batch_map_parameters(
    obj: CircuitOrExtractedParameters,
    inputs: Iterable[Tensor],
    weights: Iterable[Tensor],
) -> Iterable[Arguments]:
    extracted_parameters = _get_extracted_parameters(obj)

    return map(map_parameters, itertools.repeat(extracted_parameters), inputs, weights)


def is_single_layer_circuit(weights: Tensor) -> bool:
    return len(weights.shape) == 1
