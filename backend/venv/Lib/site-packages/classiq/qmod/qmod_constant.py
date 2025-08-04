import inspect
from dataclasses import is_dataclass
from typing import TYPE_CHECKING, Any, Optional, cast, get_origin

from classiq.interface.exceptions import ClassiqError, ClassiqValueError
from classiq.interface.generator.constant import Constant
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.classical_type import ClassicalArray

from classiq.qmod.cparam import CArray, CParamScalar
from classiq.qmod.declaration_inferrer import python_type_to_qmod
from classiq.qmod.generative import (
    get_frontend_interpreter,
    interpret_expression,
    is_generative_mode,
)
from classiq.qmod.model_state_container import QMODULE, ModelStateContainer
from classiq.qmod.qmod_parameter import CParam, CParamList, CParamStruct
from classiq.qmod.symbolic_expr import SymbolicExpr
from classiq.qmod.utilities import qmod_val_to_expr_str

QMODULE_ERROR_MESSAGE = (
    "Error trying to add a constant to a model without a current QModule."
)


class QConstant(SymbolicExpr):
    CURRENT_QMODULE: Optional[ModelStateContainer] = None

    def __init__(self, name: str, py_type: type, value: Any) -> None:
        super().__init__(name, False)
        self.name = name
        self._py_type = py_type
        self._value = value

    @staticmethod
    def set_current_model(qmodule: ModelStateContainer) -> None:
        QConstant.CURRENT_QMODULE = qmodule

    def add_to_model(self) -> None:
        from classiq.qmod.builtins.constants import __all__ as builtin_constants
        from classiq.qmod.semantics.validation.constants_validation import (
            check_duplicate_constants,
        )

        if self.name in builtin_constants or QConstant.CURRENT_QMODULE is None:
            return

        expr = qmod_val_to_expr_str(self._value)
        if (
            self.name in QConstant.CURRENT_QMODULE.constants
            and expr != QConstant.CURRENT_QMODULE.constants[self.name].value.expr
        ):
            raise ClassiqError(f"Constant {self.name} is already defined in the model")

        constant = self._get_constant_node()
        QConstant.CURRENT_QMODULE.constants[self.name] = constant
        check_duplicate_constants([constant])
        if is_generative_mode():
            get_frontend_interpreter().add_constant(constant)

    def _get_constant_node(self) -> Constant:
        if isinstance(self._value, QConstant):
            if QConstant.CURRENT_QMODULE is None:
                raise ClassiqError(QMODULE_ERROR_MESSAGE)
            return Constant(
                name=self.name,
                const_type=QConstant.CURRENT_QMODULE.constants[
                    self._value.name
                ].const_type,
                value=Expression(expr=self._value.name),
            )

        qmod_type = python_type_to_qmod(
            self._py_type, qmodule=QConstant.CURRENT_QMODULE
        )
        if qmod_type is None:
            raise ClassiqError("Invalid QMOD type")

        expr = qmod_val_to_expr_str(self._value)
        return Constant(
            name=self.name,
            const_type=qmod_type,
            value=Expression(expr=expr),
        )

    def __getattr__(self, name: str) -> CParam:
        self.add_to_model()

        if name == "is_quantum":
            return False  # type:ignore[return-value]

        py_type = type(self._value)
        if (
            QConstant.CURRENT_QMODULE is None
            or not inspect.isclass(py_type)
            or not is_dataclass(py_type)
        ):
            return self.__getattribute__(name)

        return CParamStruct.get_field(
            QConstant.CURRENT_QMODULE, self.name, py_type.__name__, name
        )

    def __getitem__(self, item: Any) -> CParam:
        self.add_to_model()

        if QConstant.CURRENT_QMODULE is None:
            QConstant.set_current_model(QMODULE)
        if TYPE_CHECKING:
            assert QConstant.CURRENT_QMODULE is not None
        qmod_type = python_type_to_qmod(
            self._py_type, qmodule=QConstant.CURRENT_QMODULE
        )
        if qmod_type is None:
            raise ClassiqError("Invalid QMOD type")

        if not isinstance(qmod_type, ClassicalArray):
            raise ClassiqError("Invalid subscript to non-list constant")

        return CParamList(
            self.name,
            qmod_type,
            QConstant.CURRENT_QMODULE,
        )[item]

    def __len__(self) -> int:
        raise ClassiqValueError(
            "len(<const>) is not supported for classical constants - use <const>.len "
            "instead"
        )

    @property
    def len(self) -> int:
        self.add_to_model()
        if get_origin(self._py_type) != CArray:
            raise ClassiqValueError(
                f"Constant {self.name!r} of type {self._py_type.__name__!r} does not "
                f"have a 'len' property"
            )
        len_expr = f"get_field({self.name}, 'len')"
        if is_generative_mode():
            return interpret_expression(len_expr)
        return cast(int, CParamScalar(len_expr))

    def __str__(self) -> str:
        self.add_to_model()
        return super().__str__()
