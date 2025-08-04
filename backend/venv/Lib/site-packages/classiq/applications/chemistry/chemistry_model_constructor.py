from collections.abc import Mapping
from typing import Optional, cast

from classiq.interface.chemistry.fermionic_operator import (
    FermionicOperator,
    SummedFermionicOperator,
)
from classiq.interface.chemistry.ground_state_problem import (
    CHEMISTRY_PROBLEMS_TYPE,
    HamiltonianProblem,
    MoleculeProblem,
)
from classiq.interface.chemistry.molecule import Atom
from classiq.interface.exceptions import ClassiqError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.function_params import IOName
from classiq.interface.generator.functions.classical_type import (
    ClassicalArray,
    Real,
)
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.generator.functions.type_modifier import TypeModifier
from classiq.interface.model.allocate import Allocate
from classiq.interface.model.classical_parameter_declaration import (
    ClassicalParameterDeclaration,
)
from classiq.interface.model.handle_binding import HandleBinding
from classiq.interface.model.model import Model, SerializedModel
from classiq.interface.model.native_function_definition import NativeFunctionDefinition
from classiq.interface.model.port_declaration import PortDeclaration
from classiq.interface.model.quantum_function_call import QuantumFunctionCall
from classiq.interface.model.quantum_lambda_function import QuantumLambdaFunction
from classiq.interface.model.quantum_statement import QuantumStatement

from classiq.applications.chemistry.ansatz_parameters import (
    AnsatzParameters,
    HEAParameters,
    HVAParameters,
    UCCParameters,
)
from classiq.applications.chemistry.chemistry_execution_parameters import (
    ChemistryExecutionParameters,
)
from classiq.qmod.builtins.enums import (
    Element,
    FermionMapping,
)
from classiq.qmod.builtins.structs import (
    ChemistryAtom as QmodChemistryAtom,
    Molecule as QmodMolecule,
    MoleculeProblem as QmodMoleculeProblem,
    Position as QmodPosition,
)
from classiq.qmod.global_declarative_switch import set_global_declarative_switch
from classiq.qmod.utilities import qmod_val_to_expr_str

# isort: split

# This import causes a circular import if done earlier. We use isort: split to avoid it
from classiq.open_library.functions.hea import full_hea

with set_global_declarative_switch():
    _FULL_HEA = cast(
        NativeFunctionDefinition, full_hea.create_model().function_dict["full_hea"]
    )

_LADDER_OPERATOR_TYPE_INDICATOR_TO_QMOD_MAPPING: dict[str, str] = {
    "+": "PLUS",
    "-": "MINUS",
}

_CHEMISTRY_PROBLEM_PREFIX_MAPPING: dict[type[CHEMISTRY_PROBLEMS_TYPE], str] = {
    MoleculeProblem: "molecule",
    HamiltonianProblem: "fock_hamiltonian",
}

_ANSATZ_PARAMETERS_FUNCTION_NAME_MAPPING: dict[type[AnsatzParameters], str] = {
    UCCParameters: "ucc",
    HVAParameters: "hva",
}

_EXECUTION_RESULT = "vqe_result"
_MOLECULE_PROBLEM_RESULT = "molecule_result"

_HAE_GATE_MAPPING: dict[str, QuantumFunctionCall] = {
    "h": QuantumFunctionCall(
        function="H",
        positional_args=[HandleBinding(name="q")],
    ),
    "x": QuantumFunctionCall(
        function="X",
        positional_args=[HandleBinding(name="q")],
    ),
    "y": QuantumFunctionCall(
        function="Y",
        positional_args=[HandleBinding(name="q")],
    ),
    "z": QuantumFunctionCall(
        function="Z",
        positional_args=[HandleBinding(name="q")],
    ),
    "i": QuantumFunctionCall(
        function="I",
        positional_args=[HandleBinding(name="q")],
    ),
    "s": QuantumFunctionCall(
        function="S",
        positional_args=[HandleBinding(name="q")],
    ),
    "t": QuantumFunctionCall(
        function="T",
        positional_args=[HandleBinding(name="q")],
    ),
    "sdg": QuantumFunctionCall(
        function="SDG",
        positional_args=[HandleBinding(name="q")],
    ),
    "tdg": QuantumFunctionCall(
        function="TDG",
        positional_args=[HandleBinding(name="q")],
    ),
    "p": QuantumFunctionCall(
        function="PHASE",
        positional_args=[HandleBinding(name="q")],
    ),
    "rx": QuantumFunctionCall(
        function="RX",
        positional_args=[Expression(expr="angle"), HandleBinding(name="q")],
    ),
    "ry": QuantumFunctionCall(
        function="RY",
        positional_args=[Expression(expr="angle"), HandleBinding(name="q")],
    ),
    "rz": QuantumFunctionCall(
        function="RZ",
        positional_args=[Expression(expr="angle"), HandleBinding(name="q")],
    ),
    "rxx": QuantumFunctionCall(
        function="RXX",
        positional_args=[Expression(expr="angle"), HandleBinding(name="q")],
    ),
    "ryy": QuantumFunctionCall(
        function="RYY",
        positional_args=[Expression(expr="angle"), HandleBinding(name="q")],
    ),
    "rzz": QuantumFunctionCall(
        function="RZZ",
        positional_args=[Expression(expr="angle"), HandleBinding(name="q")],
    ),
    "ch": QuantumFunctionCall(
        function="CH",
        positional_args=[HandleBinding(name="q1"), HandleBinding(name="q2")],
    ),
    "cx": QuantumFunctionCall(
        function="CX",
        positional_args=[HandleBinding(name="q1"), HandleBinding(name="q2")],
    ),
    "cy": QuantumFunctionCall(
        function="CY",
        positional_args=[HandleBinding(name="q1"), HandleBinding(name="q2")],
    ),
    "cz": QuantumFunctionCall(
        function="CZ",
        positional_args=[HandleBinding(name="q1"), HandleBinding(name="q2")],
    ),
    "crx": QuantumFunctionCall(
        function="CRX",
        positional_args=[
            Expression(expr="angle"),
            HandleBinding(name="q1"),
            HandleBinding(name="q2"),
        ],
    ),
    "cry": QuantumFunctionCall(
        function="CRY",
        positional_args=[
            Expression(expr="angle"),
            HandleBinding(name="q1"),
            HandleBinding(name="q2"),
        ],
    ),
    "crz": QuantumFunctionCall(
        function="CRZ",
        positional_args=[
            Expression(expr="angle"),
            HandleBinding(name="q1"),
            HandleBinding(name="q2"),
        ],
    ),
    "cp": QuantumFunctionCall(
        function="CPHASE",
        positional_args=[
            Expression(expr="angle"),
            HandleBinding(name="q1"),
            HandleBinding(name="q2"),
        ],
    ),
    "swap": QuantumFunctionCall(
        function="SWAP",
        positional_args=[HandleBinding(name="q1"), HandleBinding(name="q2")],
    ),
}


def _atoms_to_qmod_atoms(atoms: list[Atom]) -> list[QmodChemistryAtom]:
    return [
        QmodChemistryAtom(
            element=Element[atom.symbol],  # type:ignore[arg-type]
            position=QmodPosition(
                x=atom.x,  # type:ignore[arg-type]
                y=atom.y,  # type:ignore[arg-type]
                z=atom.z,  # type:ignore[arg-type]
            ),
        )
        for atom in atoms
    ]


def molecule_problem_to_qmod(
    molecule_problem: MoleculeProblem,
) -> QmodMoleculeProblem:
    return QmodMoleculeProblem(
        mapping=FermionMapping[  # type:ignore[arg-type]
            molecule_problem.mapping.value.upper()
        ],
        z2_symmetries=molecule_problem.z2_symmetries,  # type:ignore[arg-type]
        molecule=QmodMolecule(
            atoms=_atoms_to_qmod_atoms(
                molecule_problem.molecule.atoms
            ),  # type:ignore[arg-type]
            spin=molecule_problem.molecule.spin,  # type:ignore[arg-type]
            charge=molecule_problem.molecule.charge,  # type:ignore[arg-type]
        ),
        freeze_core=molecule_problem.freeze_core,  # type:ignore[arg-type]
        remove_orbitals=molecule_problem.remove_orbitals,  # type:ignore[arg-type]
    )


def _fermionic_operator_to_qmod_ladder_ops(
    fermionic_operator: FermionicOperator,
) -> str:
    return "\n\t\t\t\t\t".join(
        [
            f"struct_literal(LadderOp, op=LadderOperator.{_LADDER_OPERATOR_TYPE_INDICATOR_TO_QMOD_MAPPING[ladder_op[0]]}, index={ladder_op[1]}),"
            for ladder_op in fermionic_operator.op_list
        ]
    )[:-1]


def _summed_fermionic_operator_to_qmod_lader_terms(
    hamiltonian: SummedFermionicOperator,
) -> str:
    return "\t\t".join(
        [
            f"""
            struct_literal(LadderTerm,
                coefficient={fermionic_operator[1]},
                ops=[
                    {_fermionic_operator_to_qmod_ladder_ops(fermionic_operator[0])}
                ]
            ),"""
            for fermionic_operator in hamiltonian.op_list
        ]
    )[:-1]


def _hamiltonian_problem_to_qmod_fock_hamiltonian_problem(
    hamiltonian_problem: HamiltonianProblem,
) -> str:
    mapping = FermionMapping[hamiltonian_problem.mapping.value.upper()]
    return (
        # fmt: off
        "struct_literal("
        "FockHamiltonianProblem,"
        f"mapping={qmod_val_to_expr_str(mapping)},"
        f"z2_symmetries={hamiltonian_problem.z2_symmetries},"
        f"terms=[{_summed_fermionic_operator_to_qmod_lader_terms(hamiltonian_problem.hamiltonian)}],"
        f"num_particles={hamiltonian_problem.num_particles}"
        ")"
        # fmt: on
    )


def _convert_library_problem_to_qmod_problem(problem: CHEMISTRY_PROBLEMS_TYPE) -> str:
    if isinstance(problem, MoleculeProblem):
        return qmod_val_to_expr_str(molecule_problem_to_qmod(problem))
    elif isinstance(problem, HamiltonianProblem):
        return _hamiltonian_problem_to_qmod_fock_hamiltonian_problem(problem)
    else:
        raise ClassiqError(f"Invalid problem type: {problem}")


def _get_chemistry_function(
    chemistry_problem: CHEMISTRY_PROBLEMS_TYPE,
    chemistry_function_name: str,
    inouts: Mapping[IOName, HandleBinding],
    ansatz_parameters_expressions: Optional[list[Expression]] = None,
) -> QuantumFunctionCall:
    problem_prefix = _CHEMISTRY_PROBLEM_PREFIX_MAPPING[type(chemistry_problem)]
    return QuantumFunctionCall(
        function=f"{problem_prefix}_{chemistry_function_name}",
        positional_args=[
            Expression(
                expr=_convert_library_problem_to_qmod_problem(chemistry_problem)
            ),
            *(ansatz_parameters_expressions or []),
            *inouts.values(),
        ],
    )


def _get_hartree_fock(
    chemistry_problem: CHEMISTRY_PROBLEMS_TYPE,
) -> QuantumFunctionCall:
    return _get_chemistry_function(
        chemistry_problem,
        "hartree_fock",
        {"qbv": HandleBinding(name="qbv")},
    )


def _get_hea_function(hea_parameters: HEAParameters) -> QuantumFunctionCall:
    return QuantumFunctionCall(
        function="full_hea",
        positional_args=[
            Expression(expr=f"{hea_parameters.num_qubits}"),
            Expression(
                expr=f"{[int(_is_parametric_gate(_HAE_GATE_MAPPING[gate])) for gate in hea_parameters.one_qubit_gates+hea_parameters.two_qubit_gates]}"
            ),
            Expression(expr="t"),
            Expression(
                expr=f"{[list(connectivity_pair) for connectivity_pair in hea_parameters.connectivity_map]}"
            ),
            Expression(expr=f"{hea_parameters.reps}"),
            [
                QuantumLambdaFunction(
                    pos_rename_params=["angle", "q"],
                    body=[_HAE_GATE_MAPPING[gate]],
                )
                for gate in hea_parameters.one_qubit_gates
            ],
            [
                QuantumLambdaFunction(
                    pos_rename_params=["angle", "q1", "q2"],
                    body=[_HAE_GATE_MAPPING[gate]],
                )
                for gate in hea_parameters.two_qubit_gates
            ],
            HandleBinding(name="qbv"),
        ],
    )


def _get_ansatz(
    chemistry_problem: CHEMISTRY_PROBLEMS_TYPE,
    ansatz_parameters: AnsatzParameters,
) -> QuantumFunctionCall:
    if isinstance(ansatz_parameters, HEAParameters):
        return _get_hea_function(ansatz_parameters)
    return _get_chemistry_function(
        chemistry_problem,
        _ANSATZ_PARAMETERS_FUNCTION_NAME_MAPPING[type(ansatz_parameters)],
        {"qbv": HandleBinding(name="qbv")},
        [
            Expression(expr=str(param_value))
            for param_name, param_value in ansatz_parameters.__dict__.items()
        ],
    )


def _get_chemistry_vqe_additional_params(
    execution_parameters: ChemistryExecutionParameters,
) -> str:
    return f"""maximize=False,
initial_point={execution_parameters.initial_point or list()},
optimizer=Optimizer.{execution_parameters.optimizer.value},
max_iteration={execution_parameters.max_iteration},
tolerance={execution_parameters.tolerance or 0},
step_size={execution_parameters.step_size or 0},
skip_compute_variance={execution_parameters.skip_compute_variance},
alpha_cvar=1.0,
"""


def _get_molecule_problem_execution_post_processing(
    molecule_problem: MoleculeProblem,
) -> str:
    return f"""
{_MOLECULE_PROBLEM_RESULT} = molecule_ground_state_solution_post_process({qmod_val_to_expr_str(molecule_problem_to_qmod(molecule_problem))},{_EXECUTION_RESULT})
save({{{_MOLECULE_PROBLEM_RESULT!r}: {_MOLECULE_PROBLEM_RESULT}}})
"""


def _is_parametric_gate(call: QuantumFunctionCall) -> bool:
    # FIXME: call call.params instead (CAD-21568)
    return any(
        arg for arg in call.positional_args if isinstance(arg, Expression)
    ) or any(isinstance(arg, Expression) for arg in call.positional_args)


def _get_execution_result_post_processing_statements(
    problem: CHEMISTRY_PROBLEMS_TYPE,
) -> str:
    if isinstance(problem, MoleculeProblem):
        return _get_molecule_problem_execution_post_processing(problem)
    elif isinstance(problem, HamiltonianProblem):
        return ""
    else:
        raise ClassiqError(f"Invalid problem type: {problem}")


def _count_parametric_gates(gates: list[str]) -> int:
    return sum(_is_parametric_gate(_HAE_GATE_MAPPING[gate]) for gate in gates)


def _get_hea_port_size(hea_parameters: HEAParameters) -> int:
    return hea_parameters.reps * (
        hea_parameters.num_qubits
        * _count_parametric_gates(hea_parameters.one_qubit_gates)
        + len(hea_parameters.connectivity_map)
        * _count_parametric_gates(hea_parameters.two_qubit_gates)
    )


def _get_chemistry_quantum_main_params(
    ansatz_parameters: AnsatzParameters,
) -> list[ClassicalParameterDeclaration]:
    if not isinstance(ansatz_parameters, HEAParameters):
        return []
    return [
        ClassicalParameterDeclaration(
            name="t",
            classical_type=ClassicalArray(
                element_type=Real(),
                length=Expression(expr=str(_get_hea_port_size(ansatz_parameters))),
            ),
        ),
    ]


def _get_problem_to_hamiltonian_name(chemistry_problem: CHEMISTRY_PROBLEMS_TYPE) -> str:
    problem_prefix = _CHEMISTRY_PROBLEM_PREFIX_MAPPING[type(chemistry_problem)]
    return f"{problem_prefix}_problem_to_hamiltonian"


def _get_chemistry_quantum_main(
    chemistry_problem: CHEMISTRY_PROBLEMS_TYPE,
    use_hartree_fock: bool,
    ansatz_parameters: AnsatzParameters,
) -> NativeFunctionDefinition:
    body: list[QuantumStatement] = []
    body.append(
        Allocate(
            size=Expression(
                expr=f"get_field(get_field({_get_problem_to_hamiltonian_name(chemistry_problem)}({_convert_library_problem_to_qmod_problem(chemistry_problem)})[0], 'pauli'), 'len')"
            ),
            target=HandleBinding(name="qbv"),
        ),
    )
    if use_hartree_fock:
        body.append(_get_hartree_fock(chemistry_problem))

    body.append(_get_ansatz(chemistry_problem, ansatz_parameters))

    return NativeFunctionDefinition(
        name="main",
        positional_arg_declarations=_get_chemistry_quantum_main_params(
            ansatz_parameters
        )
        + [
            PortDeclaration(
                name="qbv",
                direction=PortDeclarationDirection.Output,
                type_modifier=TypeModifier.Mutable,
            )
        ],
        body=body,
    )


def _get_chemistry_classical_code(
    chemistry_problem: CHEMISTRY_PROBLEMS_TYPE,
    execution_parameters: ChemistryExecutionParameters,
) -> str:
    qmod_problem = _convert_library_problem_to_qmod_problem(chemistry_problem)
    return (
        f"""
{_EXECUTION_RESULT} = vqe(
    hamiltonian={_get_problem_to_hamiltonian_name(chemistry_problem)}({qmod_problem}), {_get_chemistry_vqe_additional_params(execution_parameters)}
)
save({{{_EXECUTION_RESULT!r}: {_EXECUTION_RESULT}}})
"""
        + _get_execution_result_post_processing_statements(chemistry_problem)
    ).strip()


def construct_chemistry_model(
    chemistry_problem: CHEMISTRY_PROBLEMS_TYPE,
    use_hartree_fock: bool,
    ansatz_parameters: AnsatzParameters,
    execution_parameters: ChemistryExecutionParameters,
) -> SerializedModel:
    chemistry_functions = [
        _get_chemistry_quantum_main(
            chemistry_problem,
            use_hartree_fock,
            ansatz_parameters,
        )
    ]
    if isinstance(ansatz_parameters, HEAParameters):
        chemistry_functions.append(_FULL_HEA)
    model = Model(
        functions=chemistry_functions,
        classical_execution_code=_get_chemistry_classical_code(
            chemistry_problem, execution_parameters
        ),
    )
    return model.get_model()
