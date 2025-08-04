from typing import get_args

from classiq.interface.generator.expressions.evaluated_expression import (
    EvaluatedExpression,
)
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.expression_types import ExpressionValue
from classiq.interface.generator.expressions.proxies.classical.any_classical_value import (
    AnyClassicalValue,
)
from classiq.interface.model.handle_binding import HandleBinding

from classiq.evaluators.expression_evaluator import evaluate
from classiq.model_expansions.scope import (
    ClassicalSymbol,
    Evaluated,
    QuantumSymbol,
    Scope,
)


def evaluate_classical_expression(expr: Expression, scope: Scope) -> Evaluated:
    all_symbols = scope.items()
    locals_dict = (
        {
            name: EvaluatedExpression(value=evaluated.value)
            for name, evaluated in all_symbols
            if isinstance(evaluated.value, get_args(ExpressionValue))
        }
        | {
            name: EvaluatedExpression(
                value=(
                    evaluated.value.quantum_type.get_proxy(HandleBinding(name=name))
                    if evaluated.value.quantum_type.is_evaluated
                    else AnyClassicalValue(name)
                )
            )
            for name, evaluated in all_symbols
            if isinstance(evaluated.value, QuantumSymbol)
        }
        | {
            name: EvaluatedExpression(
                value=evaluated.value.classical_type.get_classical_proxy(
                    HandleBinding(name=name)
                )
            )
            for name, evaluated in all_symbols
            if isinstance(evaluated.value, ClassicalSymbol)
        }
    )

    ret = evaluate(expr, locals_dict)
    return Evaluated(value=ret.value)
