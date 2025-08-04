from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Optional

from classiq.interface.exceptions import ClassiqError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.proxies.classical.any_classical_value import (
    AnyClassicalValue,
)

from classiq.qmod.cparam import CParamScalar

if TYPE_CHECKING:
    from classiq.model_expansions.interpreters.generative_interpreter import (
        GenerativeInterpreter,
    )

_GENERATIVE_MODE: bool = False
_FRONTEND_INTERPRETER: Optional["GenerativeInterpreter"] = None


def is_generative_mode() -> bool:
    return _GENERATIVE_MODE


@contextmanager
def generative_mode_context(generative: bool) -> Iterator[None]:
    global _GENERATIVE_MODE
    previous = _GENERATIVE_MODE
    _GENERATIVE_MODE = generative
    try:
        yield
    finally:
        _GENERATIVE_MODE = previous


def set_frontend_interpreter(interpreter: "GenerativeInterpreter") -> None:
    global _FRONTEND_INTERPRETER
    _FRONTEND_INTERPRETER = interpreter


def get_frontend_interpreter() -> "GenerativeInterpreter":
    if _FRONTEND_INTERPRETER is None:
        raise ClassiqError("Interpreter was not set")
    return _FRONTEND_INTERPRETER


def interpret_expression(expr: str) -> Any:
    val = get_frontend_interpreter().evaluate(Expression(expr=expr)).value
    if isinstance(val, AnyClassicalValue):
        return CParamScalar(str(val))
    return val
