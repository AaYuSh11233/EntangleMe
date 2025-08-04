import ast

from classiq.interface.exceptions import (
    ClassiqExpansionError,
)
from classiq.interface.generator.functions.classical_type import (
    Bool,
)
from classiq.interface.model.quantum_type import QuantumBit

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.evaluators.qmod_node_evaluators.utils import (
    is_classical_type,
)


def eval_measurement(expr_val: QmodAnnotatedExpression, node: ast.Call) -> None:
    if len(node.args) != 1 or len(node.keywords) != 0:
        raise ClassiqExpansionError("'measure' expects one positional argument")
    arg_type = expr_val.get_type(node.args[0])
    if is_classical_type(arg_type):
        raise ClassiqExpansionError("'measure' expects a quantum input")
    if not isinstance(arg_type, QuantumBit):
        raise ClassiqExpansionError("Currently, 'measure' only supports quantum bits")
    expr_val.set_type(node, Bool())
