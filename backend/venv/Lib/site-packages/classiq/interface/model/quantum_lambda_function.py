from typing import TYPE_CHECKING, Callable, Optional, Union

import pydantic

from classiq.interface.ast_node import ASTNode
from classiq.interface.exceptions import ClassiqError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.helpers.backward_compatibility import zip_strict
from classiq.interface.model.quantum_function_declaration import (
    AnonQuantumOperandDeclaration,
)

if TYPE_CHECKING:
    from classiq.interface.model.statement_block import StatementBlock


class QuantumLambdaFunction(ASTNode):
    """
    The definition of an anonymous function passed as operand to higher-level functions
    """

    pos_rename_params: list[str] = pydantic.Field(
        default_factory=list,
        description="Mapping of the declared param to the actual variable name used",
    )

    body: "StatementBlock" = pydantic.Field(
        description="A list of function calls passed to the operator"
    )

    _func_decl: Optional[AnonQuantumOperandDeclaration] = pydantic.PrivateAttr(
        default=None
    )

    _py_callable: Callable = pydantic.PrivateAttr(default=None)

    @property
    def py_callable(self) -> Callable:
        return self._py_callable

    def is_generative(self) -> bool:
        return self.py_callable is not None

    def set_py_callable(self, py_callable: Callable) -> None:
        self._py_callable = py_callable

    @property
    def func_decl(self) -> AnonQuantumOperandDeclaration:
        if self._func_decl is None:
            raise ClassiqError("Could not resolve lambda signature.")
        return self._func_decl

    def set_op_decl(self, fd: AnonQuantumOperandDeclaration) -> None:
        self._func_decl = fd

    @property
    def named_func_decl(self) -> AnonQuantumOperandDeclaration:
        named_params = [
            param.rename(rename)
            for param, rename in zip_strict(
                self.func_decl.positional_arg_declarations,
                self.pos_rename_params,
                strict=False,  # strict=False enables lambda keyword args
            )
        ]
        return self.func_decl.model_copy(
            update={"positional_arg_declarations": named_params}
        )


class OperandIdentifier(ASTNode):
    name: str
    index: Expression

    def __str__(self) -> str:
        return f"{self.name}[{self.index.expr}]"


QuantumCallable = Union[str, OperandIdentifier, QuantumLambdaFunction]
QuantumOperand = Union[QuantumCallable, list[QuantumCallable]]
