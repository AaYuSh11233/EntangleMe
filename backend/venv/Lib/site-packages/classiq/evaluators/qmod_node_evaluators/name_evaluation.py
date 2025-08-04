import ast
from typing import Any

import sympy

from classiq.interface.exceptions import (
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.expressions.proxies.classical.qmod_struct_instance import (
    QmodStructInstance,
)
from classiq.interface.generator.functions.classical_type import (
    ClassicalType,
)
from classiq.interface.model.handle_binding import HandleBinding
from classiq.interface.model.quantum_type import QuantumType

from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.evaluators.qmod_type_inference.classical_type_inference import (
    infer_classical_type,
)


def eval_name(expr_val: QmodAnnotatedExpression, node: ast.Name, value: Any) -> None:
    # FIXME: Remove sympy compatibility (CLS-3214)
    if isinstance(
        value, (bool, int, float, complex, list, QmodStructInstance, sympy.Basic)
    ):
        expr_val.set_type(node, infer_classical_type(value))
        expr_val.set_value(node, value)
    elif isinstance(value, (ClassicalType, QuantumType)):  # type:ignore[unreachable]
        expr_val.set_type(node, value)
        expr_val.set_var(node, HandleBinding(name=node.id))
    else:
        raise ClassiqInternalExpansionError
