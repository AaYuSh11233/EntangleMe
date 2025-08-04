import json
from typing import Any

from classiq.interface.exceptions import ClassiqInternalExpansionError
from classiq.interface.generator.expressions.proxies.classical.classical_proxy import (
    ClassicalProxy,
)
from classiq.interface.generator.expressions.proxies.classical.classical_struct_proxy import (
    ClassicalStructProxy,
)
from classiq.interface.generator.expressions.proxies.classical.utils import (
    get_proxy_type,
)
from classiq.interface.model.quantum_function_declaration import (
    NamedParamsQuantumFunctionDeclaration,
)
from classiq.interface.model.quantum_type import QuantumNumeric

from classiq.model_expansions.closure import FunctionClosure
from classiq.model_expansions.scope import (
    Evaluated,
    QuantumSymbol,
    evaluated_to_str as evaluated_classical_param_to_str,
)


def get_func_call_cache_key(
    decl: NamedParamsQuantumFunctionDeclaration,
    args: list[Evaluated],
) -> str:
    if len(decl.positional_arg_declarations) != len(args):
        raise ClassiqInternalExpansionError(
            "Mismatch between number of args to number of arg declarations"
        )
    return f"{decl.name}__{_evaluated_args_to_str(args)}"


def _evaluated_args_to_str(evaluated_args: list[Evaluated]) -> str:
    args_signature = [
        _evaluated_arg_to_str(eval_arg.value) for eval_arg in evaluated_args
    ]
    return json.dumps(args_signature)


def _evaluated_arg_to_str(arg: Any) -> str:
    if isinstance(arg, str):
        return arg
    if isinstance(arg, QuantumSymbol):
        return _evaluated_quantum_symbol_to_str(arg)
    if isinstance(arg, FunctionClosure):
        return _evaluated_one_operand_to_str(arg)
    if isinstance(arg, list) and arg and isinstance(arg[0], FunctionClosure):
        return _evaluated_operands_list_to_str(arg)
    if isinstance(arg, ClassicalProxy):
        if isinstance(arg, ClassicalStructProxy):
            return repr(arg.struct_declaration)
        return repr(get_proxy_type(arg))
    return evaluated_classical_param_to_str(arg)


def _evaluated_quantum_symbol_to_str(port: QuantumSymbol) -> str:
    res = port.quantum_type.model_dump_json(exclude_none=True, exclude={"name"})
    if (
        isinstance(port.quantum_type, QuantumNumeric)
        and (bounds := port.quantum_type.get_bounds()) is not None
    ):
        res += f"_{float(bounds[0])}_{float(bounds[1])}"
    return res


def _evaluated_one_operand_to_str(operand: FunctionClosure) -> str:
    return operand.name


def _evaluated_operands_list_to_str(arg: list[FunctionClosure]) -> str:
    return json.dumps([_evaluated_one_operand_to_str(ope) for ope in arg])
