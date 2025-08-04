from typing import TYPE_CHECKING, Literal, Optional

import pydantic

from classiq.interface.ast_node import ASTNodeType, reset_lists
from classiq.interface.generator.arith.arithmetic import compute_arithmetic_result_type
from classiq.interface.model.quantum_expressions.quantum_expression import (
    QuantumExpressionOperation,
)
from classiq.interface.model.quantum_type import QuantumType

if TYPE_CHECKING:
    from classiq.interface.model.statement_block import StatementBlock


class Control(QuantumExpressionOperation):
    kind: Literal["Control"]
    body: "StatementBlock"
    else_block: Optional["StatementBlock"] = None

    _ctrl_size: int = pydantic.PrivateAttr(default=0)
    _result_type: Optional[QuantumType] = pydantic.PrivateAttr(
        default=None,
    )

    @property
    def ctrl_size(self) -> int:
        return self._ctrl_size

    def set_ctrl_size(self, ctrl_size: int) -> None:
        self._ctrl_size = ctrl_size

    @property
    def result_type(self) -> QuantumType:
        assert self._result_type is not None
        return self._result_type

    def initialize_var_types(
        self,
        var_types: dict[str, QuantumType],
        machine_precision: int,
    ) -> None:
        super().initialize_var_types(var_types, machine_precision)
        self._result_type = compute_arithmetic_result_type(
            self.expression.expr, var_types, machine_precision
        )

    def _as_back_ref(self: ASTNodeType) -> ASTNodeType:
        return reset_lists(self, ["body", "else_block"])
