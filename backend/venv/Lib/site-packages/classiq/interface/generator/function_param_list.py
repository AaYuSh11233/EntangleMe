import itertools

from classiq.interface.generator.amplitude_loading import AmplitudeLoading
from classiq.interface.generator.arith.arithmetic import Arithmetic
from classiq.interface.generator.arith.binary_ops import (
    Adder,
    BitwiseAnd,
    BitwiseOr,
    BitwiseXor,
    CyclicShift,
    Equal,
    GreaterEqual,
    GreaterThan,
    LessEqual,
    LessThan,
    LShift,
    Modulo,
    Multiplier,
    NotEqual,
    Power,
    RShift,
    Subtractor,
)
from classiq.interface.generator.arith.extremum_operations import Max, Min
from classiq.interface.generator.arith.logical_ops import LogicalAnd, LogicalOr
from classiq.interface.generator.arith.unary_ops import BitwiseInvert, Negation, Sign
from classiq.interface.generator.commuting_pauli_exponentiation import (
    CommutingPauliExponentiation,
)
from classiq.interface.generator.copy import Copy
from classiq.interface.generator.entangler_params import (
    GridEntangler,
    HypercubeEntangler,
    TwoDimensionalEntangler,
)
from classiq.interface.generator.finance import Finance, FinanceModels, FinancePayoff
from classiq.interface.generator.function_param_library import FunctionParamLibrary
from classiq.interface.generator.hadamard_transform import HadamardTransform
from classiq.interface.generator.hamiltonian_evolution.exponentiation import (
    Exponentiation,
)
from classiq.interface.generator.hamiltonian_evolution.qdrift import QDrift
from classiq.interface.generator.hamiltonian_evolution.suzuki_trotter import (
    SuzukiTrotter,
)
from classiq.interface.generator.hardware_efficient_ansatz import (
    HardwareEfficientAnsatz,
)
from classiq.interface.generator.hartree_fock import HartreeFock
from classiq.interface.generator.hva import HVA
from classiq.interface.generator.identity import Identity
from classiq.interface.generator.linear_pauli_rotations import LinearPauliRotations
from classiq.interface.generator.mcu import Mcu
from classiq.interface.generator.mcx import Mcx
from classiq.interface.generator.qft import QFT
from classiq.interface.generator.qsvm import QSVMFeatureMap
from classiq.interface.generator.randomized_benchmarking import RandomizedBenchmarking
from classiq.interface.generator.reset import Reset
from classiq.interface.generator.standard_gates.standard_gates_param_list import (
    standard_gate_function_param_library,
)
from classiq.interface.generator.standard_gates.u_gate import UGate
from classiq.interface.generator.state_preparation import (
    BellStatePreparation,
    ComputationalBasisStatePreparation,
    ExponentialStatePreparation,
    GHZStatePreparation,
    StatePreparation,
    UniformDistributionStatePreparation,
    WStatePreparation,
)
from classiq.interface.generator.ucc import UCC
from classiq.interface.generator.unitary_gate import UnitaryGate
from classiq.interface.generator.user_defined_function_params import CustomFunction

function_param_library: FunctionParamLibrary = FunctionParamLibrary(
    param_list=itertools.chain(
        {
            StatePreparation,
            ComputationalBasisStatePreparation,
            UniformDistributionStatePreparation,
            BellStatePreparation,
            GHZStatePreparation,
            WStatePreparation,
            ExponentialStatePreparation,
            QFT,
            BitwiseAnd,
            BitwiseOr,
            BitwiseXor,
            BitwiseInvert,
            Adder,
            Arithmetic,
            Sign,
            Equal,
            NotEqual,
            GreaterThan,
            GreaterEqual,
            LessThan,
            LessEqual,
            Negation,
            LogicalAnd,
            LogicalOr,
            Subtractor,
            RShift,
            LShift,
            CyclicShift,
            Modulo,
            TwoDimensionalEntangler,
            Finance,
            FinanceModels,
            FinancePayoff,
            HypercubeEntangler,
            GridEntangler,
            Mcx,
            Mcu,
            CustomFunction,
            HardwareEfficientAnsatz,
            UnitaryGate,
            LinearPauliRotations,
            Multiplier,
            Power,
            HartreeFock,
            UCC,
            Min,
            Max,
            Exponentiation,
            CommutingPauliExponentiation,
            SuzukiTrotter,
            QDrift,
            Identity,
            RandomizedBenchmarking,
            HVA,
            UGate,
            AmplitudeLoading,
            QSVMFeatureMap,
            HadamardTransform,
            Copy,
            Reset,
        },
        standard_gate_function_param_library.param_list,
    )
)
