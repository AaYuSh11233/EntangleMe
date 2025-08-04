from typing import Optional

from sympy import Add, Expr, LessThan, Symbol

from classiq.interface.combinatorial_optimization.encoding_types import EncodingType

_INEQUALITY_UPPER_LIMIT = 1


def is_constraint_sum_less_than_one(
    expression: Expr, encoding_type: Optional[EncodingType] = None
) -> bool:
    # tests the case: x_1 + ... + x_n <= 1
    return (
        isinstance(expression, LessThan)
        and isinstance(expression.args[0], Add)
        and all(isinstance(arg, Symbol) for arg in expression.args[0].args)
        and (
            expression.args[1] == _INEQUALITY_UPPER_LIMIT
            or expression.args[1] == float(_INEQUALITY_UPPER_LIMIT)
        )
        and encoding_type is None
    )
