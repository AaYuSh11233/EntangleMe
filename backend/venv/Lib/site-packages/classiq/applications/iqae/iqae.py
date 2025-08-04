from typing import Literal, Optional, cast

from classiq.interface.applications.iqae.generic_iqae import GenericIQAE
from classiq.interface.applications.iqae.iqae_result import (
    IQAEIterationData,
    IQAEResult,
)
from classiq.interface.executor.execution_preferences import ExecutionPreferences
from classiq.interface.generator.model import Constraints, Preferences
from classiq.interface.generator.quantum_program import QuantumProgram
from classiq.interface.model.model import SerializedModel

from classiq.execution import ExecutionSession
from classiq.open_library import amplitude_amplification
from classiq.qmod import (
    CInt,
    Output,
    QArray,
    QBit,
    QCallable,
)
from classiq.qmod.builtins import Z, allocate, bind, within_apply
from classiq.qmod.create_model_function import create_model
from classiq.qmod.qfunc import qfunc
from classiq.synthesis import synthesize


class IQAE:
    """
    Implementation of Iterative Quantum Amplitude Estimation [1].
    Given $A$ s.t. $A|0>_n|0> = \\sqrt{1-a}|\\psi_0>_n|0> + \\sqrt{a}|\\psi_1>_n|1>$, the algorithm estimates
    $a$ by iteratively sampling $Q^kA$, where $Q=AS_0A^{\\dagger}S_{\\psi_0}$, and $k$ is an integer variable.

    For estimating $a$, The algorithm estimates $\\theta_a$ which is defined by $a = sin^2(\\theta_a)$, so it starts with a
    confidence interval $(0, \\pi/2)$ and narrows down this interval on each iteration according to the sample results.

    References:
        [1]: Grinko, D., Gacon, J., Zoufal, C., & Woerner, S. (2019).
             Iterative Quantum Amplitude Estimation.
             `arXiv:1912.05559 <https://arxiv.org/abs/1912.05559>`.
    """

    _NUM_SHOUTS = 2048

    def __init__(
        self,
        state_prep_op: QCallable[QArray[QBit, Literal["problem_vars_size"]], QBit],
        problem_vars_size: int,
        constraints: Optional[Constraints] = None,
        preferences: Optional[Preferences] = None,
    ) -> None:
        self._state_prep_op = state_prep_op
        self._problem_vars_size: int = problem_vars_size
        self._constraints: Optional[Constraints] = constraints
        self._preferences: Optional[Preferences] = preferences
        self._model: Optional[SerializedModel] = None
        self._qprog: Optional[QuantumProgram] = None

        """
        Args:
            state_prep_op (Qfunc): implementation of the operator $A$ in Qmod.
            problem_vars_size (int): The size of the problem in terms of the number of qubits, e.g., $n$ of the first register A works on.
            constraints (Constraints): Constraints for the synthesis of the model. See Constraints (Optional).
            preferences (Preferences): Preferences for the synthesis of the model. See Preferences (Optional).
        """

    def get_model(self) -> SerializedModel:
        """
        Implement the quantum part of IQAE in terms of the Qmod Model

        Args:


        Returns:
            SerializedModel (str): A serialized model.

        """

        state_prep_op = self._state_prep_op
        problem_vars_size = self._problem_vars_size

        @qfunc
        def space_transform(est_reg: QArray) -> None:
            state_prep_op(est_reg[0 : est_reg.len - 1], est_reg[est_reg.len - 1])

        @qfunc
        def oracle(est_reg: QArray) -> None:
            Z(est_reg[est_reg.len - 1])

        @qfunc
        def main(
            k: CInt,
            indicator: Output[QBit],
        ) -> None:
            est_reg: QArray = QArray("est_reg")
            problem_vars: QArray = QArray("problem_vars", length=problem_vars_size)
            allocate(problem_vars)
            allocate(indicator)
            within_apply(
                lambda: bind([problem_vars, indicator], est_reg),
                lambda: amplitude_amplification(
                    k,
                    oracle,
                    space_transform,
                    est_reg,
                ),
            )

        if self._model is None:
            self._model = create_model(
                main,
                constraints=self._constraints,
                preferences=self._preferences,
            )
        return self._model

    def get_qprog(self) -> QuantumProgram:
        """
        Create an executable quantum Program for IQAE.

        Args:

        Returns:
            QuantumProgram (QuantumProgram): Quantum program. See QuantumProgram.
        """

        if self._qprog is None:
            model = self.get_model()
            self._qprog = synthesize(model)
        return self._qprog

    def run(
        self,
        epsilon: float,
        alpha: float,
        execution_preferences: Optional[ExecutionPreferences] = None,
    ) -> IQAEResult:
        """
        Executes IQAE's quantum program with the provided epsilon, alpha, and execution
        preferences.
        If execution_preferences has been proved, or if it does not contain num_shot, then num_shot is set to 2048.

        Args:
            epsilon (float): Target accuracy in therm of $\\theta_a$ e.g $a = sin^2(\\theta_a \\pm \\epsilon)$ .
            alpha (float): Specifies the confidence level (1 - alpha)
            execution_preferences (Preferences): Preferences for the execution of the model. See ExecutionPreferences (Optional).
        Returns:
            IQAEResult (IQAEResult): A result of the IQAE algorithm. See IQAEResult.
        """

        if self._qprog is None:
            self._qprog = self.get_qprog()

        if execution_preferences is None:
            execution_preferences = ExecutionPreferences(
                num_shots=self._NUM_SHOUTS,
            )
        elif execution_preferences.num_shots is None:
            execution_preferences.num_shots = self._NUM_SHOUTS

        return self._run(
            epsilon=epsilon,
            alpha=alpha,
            execution_preferences=execution_preferences,
            quantum_program=self._qprog,
        )

    def _run(
        self,
        epsilon: float,
        alpha: float,
        execution_preferences: ExecutionPreferences,
        quantum_program: QuantumProgram,
    ) -> IQAEResult:

        iterations_data: list[IQAEIterationData] = []
        warnings: list[str] = []
        with ExecutionSession(quantum_program, execution_preferences) as executor:

            def _iqae_sample(k: int, _: int) -> int:
                sample_results = executor.sample({"k": k})
                iterations_data.append(
                    IQAEIterationData(
                        grover_iterations=k,
                        sample_results=sample_results,
                    )
                )
                return sample_results.counts_of_output("indicator").get("1", 0)

            iqae = GenericIQAE(
                epsilon=epsilon,
                alpha=alpha,
                num_shots=cast(int, execution_preferences.num_shots),
                sample_callable=_iqae_sample,
            )

            try:
                iqae.run()
            except RuntimeError as ex:
                warnings.append(f"Algorithm error: {ex.args[0]}")

        return IQAEResult(
            estimation=iqae.current_estimation(),
            confidence_interval=iqae.current_estimation_confidence_interval().tolist(),
            iterations_data=iterations_data,
            warnings=warnings,
        )
