import copy
from itertools import chain, product
from typing import Callable, Union

import pyomo.environ as pyo
from pyomo.core.base.var import VarData
from pyomo.core.expr.numeric_expr import ExpressionBase
from pyomo.core.expr.relational_expr import EqualityExpression

from classiq.interface.combinatorial_optimization.encoding_types import EncodingType
from classiq.interface.combinatorial_optimization.solver_types import QSolver
from classiq.interface.exceptions import ClassiqCombOptInvalidEncodingTypeError

from classiq.applications.combinatorial_helpers import encoding_utils, pyomo_utils
from classiq.applications.combinatorial_helpers.encoding_mapping import EncodingMapping
from classiq.applications.combinatorial_helpers.encoding_utils import ONE_HOT_SUFFIX


def _make_invalid_encoding_type_error(
    encoding_type: EncodingType,
) -> ClassiqCombOptInvalidEncodingTypeError:
    return ClassiqCombOptInvalidEncodingTypeError(
        encoding_type=encoding_type,
        valid_types=EncodingType.__members__.keys(),
    )


def encoding_length(var: VarData, encoding_type: Union[EncodingType, None]) -> int:
    if encoding_type is None:
        return 1

    var_span = encoding_utils.get_var_span(var)

    if encoding_type == EncodingType.BINARY:
        return var_span.bit_length()

    elif encoding_type == EncodingType.ONE_HOT:
        return var_span + 1

    else:
        raise _make_invalid_encoding_type_error(encoding_type)


class ModelEncoder:
    def __init__(
        self,
        model: pyo.ConcreteModel,
        qsolver: QSolver,
        encoding_type: EncodingType = EncodingType.BINARY,
    ) -> None:
        self.encoding_type = encoding_type
        self.encoded_model = copy.deepcopy(model)
        self.qsolver = qsolver
        self.vars_original = list(self.encoded_model.component_objects(pyo.Var))
        self.vars_encoding_mapping = self._encode_variables()
        if self.encoding_type == EncodingType.ONE_HOT:
            self._add_one_hot_constraints()
        self._encode_constraints()
        self._encode_objective()

    @property
    def _shift_substitution_dict(self) -> dict[int, pyo.Expression]:
        variables = pyomo_utils.extract(self.encoded_model, pyo.Var)
        return {id(var): var + var.lb for var in variables}

    def _encode_variables(self) -> EncodingMapping:
        vars_encoding_mapping = EncodingMapping(self.encoding_type)
        for variable in self.vars_original:
            # encode variables
            encoded_var_name = encoding_utils.encoded_obj_name(variable.name)
            encoded_var = pyo.Var(self._get_encoding_idxs(variable), domain=pyo.Binary)
            setattr(self.encoded_model, encoded_var_name, encoded_var)

            # create mapping between original variables and their encodings
            for var_idx, var_data in variable.items():
                encoding_vars = [
                    encoded_var[var_idx, encoding_idx]
                    for encoding_idx in range(
                        encoding_length(var_data, self.encoding_type)
                    )
                ]

                encoding_expr = self._get_encoding_expr(var_data, encoding_vars)

                self._add_expr_constraint(
                    constraint_name=var_data.name
                    + encoding_utils.ENCODED_SUFFIX
                    + encoding_utils.CONSTRAINT_SUFFIX,
                    expr=EqualityExpression(args=[var_data, encoding_expr]),
                )

                vars_encoding_mapping.add(
                    original_var=var_data,
                    encoding_expr=encoding_expr,
                    encodings_vars=encoding_vars,
                )
        return vars_encoding_mapping

    def _get_encoding_expr(
        self, var_data: VarData, encoding_vars: list[VarData]
    ) -> pyo.Expression:
        if self.encoding_type == EncodingType.BINARY:
            var_span = encoding_utils.get_var_span(var_data)
            coeffs = self._get_binary_coeffs(encoding_vars, var_span)

        elif self.encoding_type == EncodingType.ONE_HOT:
            coeffs = list(range(len(encoding_vars)))
        else:
            raise _make_invalid_encoding_type_error(self.encoding_type)

        encoding_expr = sum(
            coeff * encoding_var for coeff, encoding_var in zip(coeffs, encoding_vars)
        )

        # Encodes variable shift
        encoding_expr += var_data.lb
        return encoding_expr

    def _get_binary_coeffs(
        self, encoding_vars: list[VarData], var_span: int
    ) -> list[int]:
        num_vars = len(encoding_vars)
        if self.qsolver == QSolver.QAOAMixer:
            return [2**idx for idx in range(num_vars)]

        else:  # self.qsolver == QSolver.QAOAPenalty:
            coeffs = [2**idx for idx in range(num_vars - 1)]
            coeffs += [var_span - sum(coeffs)]
            return coeffs

    def _get_encoding_idxs(self, variable: pyo.Var) -> list[tuple[int, int]]:
        return list(
            chain(
                *[
                    product(
                        [var_idx], range(encoding_length(var_data, self.encoding_type))
                    )
                    for var_idx, var_data in variable.items()
                ]
            )
        )

    def _add_one_hot_constraints(self) -> None:
        for variable in self.vars_original:
            # potential bug with creating function inside a loop.
            # solved with early binding - https://stackoverflow.com/questions/3431676/creating-functions-in-a-loop
            def one_hot_rule(var_idx: int, var: pyo.Var = variable) -> ExpressionBase:
                var_data = var[var_idx]
                return sum(self.vars_encoding_mapping.get_encoding_vars(var_data)) == 1

            self._add_rule_constraint(
                constraint_name=variable.name + ONE_HOT_SUFFIX,
                idxs=getattr(self.encoded_model, variable.index),
                rule=one_hot_rule,
            )

    def _add_rule_constraint(
        self, constraint_name: str, idxs: list[int], rule: Callable
    ) -> None:
        encoding_constraint = pyo.Constraint(idxs, rule=rule)

        setattr(self.encoded_model, constraint_name, encoding_constraint)

    def _add_expr_constraint(self, constraint_name: str, expr: ExpressionBase) -> None:
        setattr(self.encoded_model, constraint_name, pyo.Constraint(expr=expr))

    def _encode_objective(self) -> None:
        encoding_utils.encode_objective(
            self.encoded_model, self.vars_encoding_mapping.substitution_dict
        )

    def encode_expr(
        self,
        expr: pyo.Expression,
        substitution_dict: Union[dict[int, pyo.Expression], None] = None,
    ) -> pyo.Expression:
        if substitution_dict is None:
            substitution_dict = self.vars_encoding_mapping.substitution_dict
        return encoding_utils.encode_expr(expr, substitution_dict)

    def _encode_constraints(self) -> None:
        if self.qsolver == QSolver.QAOAPenalty:
            return

        encoding_utils.encode_constraints(
            self.encoded_model, self._shift_substitution_dict
        )
