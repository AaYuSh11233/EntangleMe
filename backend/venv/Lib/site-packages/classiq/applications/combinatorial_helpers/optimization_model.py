import copy
from functools import cached_property
from itertools import filterfalse
from typing import Optional, Union

import pyomo.environ as pyo
import sympy
from pyomo.core import ConcreteModel
from pyomo.core.base.constraint import _GeneralConstraintData
from pyomo.core.base.var import VarData
from pyomo.core.expr.sympy_tools import sympyify_expression
from pyomo.environ import Expression

from classiq.interface.chemistry.operator import PauliOperator
from classiq.interface.combinatorial_optimization import sense
from classiq.interface.combinatorial_optimization.encoding_types import EncodingType
from classiq.interface.combinatorial_optimization.solver_types import QSolver
from classiq.interface.exceptions import ClassiqCombOptError

from classiq.applications.combinatorial_helpers import (
    encoding_utils,
    memory,
    pyomo_utils,
)
from classiq.applications.combinatorial_helpers.encoding_mapping import EncodingMapping
from classiq.applications.combinatorial_helpers.memory import InternalQuantumReg
from classiq.applications.combinatorial_helpers.pyomo_utils import (
    get_field_name,
    index_as_tuple,
    is_index_var,
)
from classiq.applications.combinatorial_helpers.transformations import (
    encoding,
    ising_converter,
    penalty,
    slack_variables,
)
from classiq.applications.combinatorial_helpers.transformations.fixed_variables import (
    add_fixed_variables_to_solution,
    remove_fixed_variables,
)
from classiq.applications.combinatorial_helpers.transformations.penalty_support import (
    is_model_penalty_supported,
)


class OptimizationModel:
    def __init__(
        self,
        model: ConcreteModel,
        qsolver: QSolver,
        penalty_energy: Optional[float],
        encoding_type: Optional[EncodingType] = None,
    ) -> None:
        assert model.nobjectives() == 1, "model must have a single objective"
        model_copy = copy.deepcopy(model)
        self._model_original = model
        self._assigned_model = remove_fixed_variables(model_copy)
        self.qsolver = qsolver
        self._encoding_type = encoding_type

        self.is_encoded = encoding_utils.is_model_encodable(model_copy)
        if self.is_encoded:
            if self._encoding_type is None:
                self._encoding_type = EncodingType.BINARY
            self._model_encoder = encoding.ModelEncoder(
                model_copy, qsolver, self._encoding_type
            )
            self._model = self._model_encoder.encoded_model
            self._vars_encoding_mapping = self._model_encoder.vars_encoding_mapping
        else:
            self._model = model_copy
            # TODO How to handle encoding_type == None
            self._vars_encoding_mapping = EncodingMapping(self._encoding_type)  # type: ignore[arg-type]

        self._slack_vars_convert()

        self.memory_mapping = memory.MemoryMapping(
            self.vars_not_encoded, self._vars_encoding_mapping
        )

        self.is_maximization = sense.is_maximization(model_copy)
        self.penalty_energy = penalty_energy

        self.objective = next(self._model.component_objects(pyo.Objective))
        if self.qsolver == QSolver.QAOAPenalty:
            self.objective.expr += self._get_penalty_term(self.constraints)
            if self.is_encoded:
                self.objective.expr = self._model_encoder.encode_expr(
                    self.objective.expr
                )
        self._initialize_objective_not_encoded(model_copy)

    @property
    def vars(self) -> list[VarData]:
        return pyomo_utils.extract(self._model, VarData)

    @property
    def vars_not_encoded(self) -> list[VarData]:
        return list(filterfalse(encoding_utils.is_obj_encoded, self.vars))

    @property
    def _ising_vars(self) -> list[VarData]:
        if self.is_encoded:
            return [
                var
                for var in self.vars
                if encoding_utils.is_obj_encoded(var)
                or slack_variables.is_obj_slacked(var)
            ]
        else:
            return self.vars

    @property
    def constraints(self) -> list[_GeneralConstraintData]:
        all_constraints = pyomo_utils.extract(self._model, _GeneralConstraintData)
        return list(filterfalse(encoding_utils.is_obj_encoded, all_constraints))

    @property
    def qregs(self) -> list[InternalQuantumReg]:
        return self.memory_mapping.qregs

    @property
    def num_qubits(self) -> int:
        return sum(qreg.size for qreg in self.qregs)

    @property
    def sign(self) -> int:
        return -1 if self.is_maximization else 1

    def _get_penalty_term(
        self, constraints: list[_GeneralConstraintData]
    ) -> Union[int, Expression]:
        normalized_penalty_term = penalty.get_penalty_expression(constraints)
        return self.penalty_energy * normalized_penalty_term * self.sign

    @cached_property
    def ising(self) -> PauliOperator:
        return (
            ising_converter.convert_pyomo_to_hamiltonian(
                self.objective.expr, self._ising_vars, self.qregs
            )
            * self.sign
        )

    def _remove_slack_variables_from_solution(self, solution: list[int]) -> list[int]:
        variables = pyomo_utils.extract(self._model_original, pyo.Var)
        return solution[: len(variables)]

    def decode(self, solution: list[int]) -> list[int]:
        if self.is_encoded:
            solution = self._vars_encoding_mapping.decode(solution)

        solution = add_fixed_variables_to_solution(self._model_original, solution)

        return self._remove_slack_variables_from_solution(solution)

    def get_operator(self) -> PauliOperator:
        try:
            return self.ising
        except Exception as exc:
            raise ClassiqCombOptError(
                f"Could not convert optimization model to operator: {exc}"
            ) from exc

    def _slack_vars_convert(self) -> ConcreteModel:
        if self.qsolver == QSolver.QAOAPenalty and not is_model_penalty_supported(
            self._model
        ):
            return slack_variables.slack_vars_convert(self._model)

    def _initialize_objective_not_encoded(self, model_copy: pyo.ConcreteModel) -> None:
        objective_not_encoded = next(model_copy.component_objects(pyo.Objective))
        objective_map, objective_expr = sympyify_expression(objective_not_encoded)
        objective_expr *= self.sign
        if self.qsolver == QSolver.QAOAPenalty:
            penalty = self._get_penalty_term(self.constraints)
            penalty_map, penalty_expr = sympyify_expression(penalty)
            objective_expr += penalty_expr * self.sign
            objective_map.sympy2pyomo |= penalty_map.sympy2pyomo
            for key, value in penalty_map.pyomo2sympy.items():
                objective_map.pyomo2sympy[key] = value
        sympy_renaming = {
            var: sympy.Symbol(str(var).replace(",", "_").replace("'", "_"))
            for var in objective_expr.free_symbols
        }
        objective_expr = objective_expr.subs(sympy_renaming)
        sympy_mapping = {
            sympy_renaming[sympy_var]: (
                get_field_name(pyomo_var)
                if not is_index_var(pyomo_var)
                else (
                    get_field_name(pyomo_var.parent_component()),
                    index_as_tuple(pyomo_var.index()),
                )
            )
            for pyomo_var, sympy_var in objective_map.pyomo2sympy.items()
        }
        compiled_expr = compile(str(objective_expr), "<string>", "eval")
        self.objective_not_encoded_sympy = sympy_mapping, objective_expr, compiled_expr
