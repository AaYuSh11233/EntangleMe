from typing import Literal, Union

from classiq.interface.enum_utils import StrEnum


class AnalyzerProviderVendor(StrEnum):
    IBM_QUANTUM = "IBM Quantum"
    AZURE_QUANTUM = "Azure Quantum"
    AMAZON_BRAKET = "Amazon Braket"


class ProviderVendor(StrEnum):
    CLASSIQ = "Classiq"
    IBM_QUANTUM = "IBM Quantum"
    AZURE_QUANTUM = "Azure Quantum"
    AMAZON_BRAKET = "Amazon Braket"
    IONQ = "IonQ"
    GOOGLE = "Google"
    ALICE_AND_BOB = "Alice & Bob"
    OQC = "OQC"
    INTEL = "Intel"
    AQT = "AQT"
    IQCC = "IQCC"
    CINECA = "CINECA"


class ProviderTypeVendor:
    CLASSIQ = Literal[ProviderVendor.CLASSIQ]
    IBM_CLOUD = Literal[ProviderVendor.IBM_QUANTUM]
    AZURE_QUANTUM = Literal[ProviderVendor.AZURE_QUANTUM]
    AMAZON_BRAKET = Literal[ProviderVendor.AMAZON_BRAKET]
    IONQ = Literal[ProviderVendor.IONQ]
    GOOGLE = Literal[ProviderVendor.GOOGLE]
    ALICE_BOB = Literal[ProviderVendor.ALICE_AND_BOB]
    OQC = Literal[ProviderVendor.OQC]
    INTEL = Literal[ProviderVendor.INTEL]
    AQT = Literal[ProviderVendor.AQT]
    IQCC = Literal[ProviderVendor.IQCC]
    CINECA = Literal[ProviderVendor.CINECA]


class ClassiqSimulatorBackendNames(StrEnum):
    """

    The simulator backends available in the Classiq provider.

    """

    SIMULATOR = "simulator"
    SIMULATOR_STATEVECTOR = "simulator_statevector"
    SIMULATOR_DENSITY_MATRIX = "simulator_density_matrix"
    SIMULATOR_MATRIX_PRODUCT_STATE = "simulator_matrix_product_state"


class IonqBackendNames(StrEnum):
    """
    IonQ backend names which Classiq Supports running on.
    """

    SIMULATOR = "simulator"
    HARMONY = "qpu.harmony"
    ARIA_1 = "qpu.aria-1"
    ARIA_2 = "qpu.aria-2"
    FORTE_1 = "qpu.forte-1"


class AzureQuantumBackendNames(StrEnum):
    """
    AzureQuantum backend names which Classiq Supports running on.
    """

    IONQ_ARIA_1 = "ionq.qpu.aria-1"
    IONQ_ARIA_2 = "ionq.qpu.aria-2"
    IONQ_QPU = "ionq.qpu"
    IONQ_QPU_FORTE = "ionq.qpu.forte-1"
    IONQ_SIMULATOR = "ionq.simulator"
    MICROSOFT_ESTIMATOR = "microsoft.estimator"
    MICROSOFT_FULLSTATE_SIMULATOR = "microsoft.simulator.fullstate"
    RIGETTI_SIMULATOR = "rigetti.sim.qvm"
    RIGETTI_ANKAA2 = "rigetti.qpu.ankaa-2"
    RIGETTI_ANKAA9 = "rigetti.qpu.ankaa-9q-1"
    QCI_MACHINE1 = "qci.machine1"
    QCI_NOISY_SIMULATOR = "qci.simulator.noisy"
    QCI_SIMULATOR = "qci.simulator"
    QUANTINUUM_API_VALIDATOR1_1 = "quantinuum.sim.h1-1sc"
    QUANTINUUM_API_VALIDATOR1_2 = "quantinuum.sim.h1-2sc"
    QUANTINUUM_API_VALIDATOR2_1 = "quantinuum.sim.h2-1sc"
    QUANTINUUM_QPU1_1 = "quantinuum.qpu.h1-1"
    QUANTINUUM_QPU1_2 = "quantinuum.qpu.h1-2"
    QUANTINUUM_SIMULATOR1_1 = "quantinuum.sim.h1-1e"
    QUANTINUUM_SIMULATOR1_2 = "quantinuum.sim.h1-2e"
    QUANTINUUM_QPU2 = "quantinuum.qpu.h2-1"
    QUANTINUUM_SIMULATOR2 = "quantinuum.sim.h2-1e"


class AmazonBraketBackendNames(StrEnum):
    """
    Amazon Braket backend names which Classiq Supports running on.
    """

    AMAZON_BRAKET_SV1 = "SV1"
    AMAZON_BRAKET_TN1 = "TN1"
    AMAZON_BRAKET_DM1 = "dm1"
    AMAZON_BRAKET_ASPEN_11 = "Aspen-11"
    AMAZON_BRAKET_M_1 = "Aspen-M-1"
    AMAZON_BRAKET_IONQ = "IonQ Device"
    AMAZON_BRAKET_LUCY = "Lucy"


# The IBM devices were taken from:
#   from qiskit_ibm_runtime.fake_provider import FakeProviderForBackendV2
#   provider = FakeProviderForBackendV2()
#   backends_list = provider.backends()
#   the_devices = ["ibm_" + backend.name.split('_')[1] for backend in backends_list.backends()]
class IBMQHardwareNames(StrEnum):
    """
    IBM backend names which Classiq Supports running on.
    """

    IBM_ALGIERS = "ibm_algiers"
    IBM_ALMADEN = "ibm_almaden"
    IBM_ARMONK = "ibm_armonk"
    IBM_ATHENS = "ibm_athens"
    IBM_AUCKLAND = "ibm_auckland"
    IBM_BELEM = "ibm_belem"
    IBM_BOEBLINGEN = "ibm_boeblingen"
    IBM_BOGOTA = "ibm_bogota"
    IBM_BRISBANE = "ibm_brisbane"
    IBM_BROOKLYN = "ibm_brooklyn"
    IBM_BURLINGTON = "ibm_burlington"
    IBM_CAIRO = "ibm_cairo"
    IBM_CAMBRIDGE = "ibm_cambridge"
    IBM_CASABLANCA = "ibm_casablanca"
    IBM_CUSCO = "ibm_cusco"
    IBM_ESSEX = "ibm_essex"
    IBM_FEZ = "ibm_fez"
    IBM_FRACTIONAL = "ibm_fractional"
    IBM_GENEVA = "ibm_geneva"
    IBM_GUADALUPE = "ibm_guadalupe"
    IBM_HANOI = "ibm_hanoi"
    IBM_JAKARTA = "ibm_jakarta"
    IBM_JOHANNESBURG = "ibm_johannesburg"
    IBM_KAWASAKI = "ibm_kawasaki"
    IBM_KOLKATA = "ibm_kolkata"
    IBM_KYIV = "ibm_kyiv"
    IBM_KYOTO = "ibm_kyoto"
    IBM_LAGOS = "ibm_lagos"
    IBM_LIMA = "ibm_lima"
    IBM_LONDON = "ibm_london"
    IBM_MANHATTAN = "ibm_manhattan"
    IBM_MANILA = "ibm_manila"
    IBM_MELBOURNE = "ibm_melbourne"
    IBM_MARRAKESH = "ibm_marrakesh"
    IBM_MONTREAL = "ibm_montreal"
    IBM_MUMBAI = "ibm_mumbai"
    IBM_NAIROBI = "ibm_nairobi"
    IBM_OSAKA = "ibm_osaka"
    IBM_OSLO = "ibm_oslo"
    IBM_OURENSE = "ibm_ourense"
    IBM_PARIS = "ibm_paris"
    IBM_PEEKSKILL = "ibm_peekskill"
    IBM_PERTH = "ibm_perth"
    IBM_PRAGUE = "ibm_prague"
    IBM_POUGHKEEPSIE = "ibm_poughkeepsie"
    IBM_QUEBEC = "ibm_quebec"
    IBM_QUITO = "ibm_quito"
    IBM_ROCHESTER = "ibm_rochester"
    IBM_ROME = "ibm_rome"
    IBM_SANTIAGO = "ibm_santiago"
    IBM_SHERBROOKE = "ibm_sherbrooke"
    IBM_SINGAPORE = "ibm_singapore"
    IBM_SYDNEY = "ibm_sydney"
    IBM_TORINO = "ibm_torino"
    IBM_TORONTO = "ibm_toronto"
    IBM_VALENCIA = "ibm_valencia"
    IBM_VIGO = "ibm_vigo"
    IBM_WASHINGTON = "ibm_washington"
    IBM_YORKTOWN = "ibm_yorktown"


class ClassiqNvidiaBackendNames(StrEnum):
    """
    Classiq's Nvidia simulator backend names.
    """

    SIMULATOR = "nvidia_simulator"
    SIMULATOR_STATEVECTOR = "nvidia_simulator_statevector"
    BRAKET_NVIDIA_SIMULATOR = "braket_nvidia_simulator"
    BRAKET_NVIDIA_SIMULATOR_STATEVECTOR = "braket_nvidia_simulator_statevector"

    def is_braket_nvidia_backend(self) -> bool:
        return self in (
            self.BRAKET_NVIDIA_SIMULATOR,
            self.BRAKET_NVIDIA_SIMULATOR_STATEVECTOR,
        )


class IntelBackendNames(StrEnum):
    SIMULATOR = "intel_qsdk_simulator"


class GoogleNvidiaBackendNames(StrEnum):
    """
    Google backend names which Classiq Supports running on.
    """

    CUQUANTUM = "cuquantum"
    CUQUANTUM_STATEVECTOR = "cuquantum_statevector"


class AliceBobBackendNames(StrEnum):
    """
    Alice & Bob backend names which Classiq Supports running on.
    """

    PERFECT_QUBITS = "PERFECT_QUBITS"
    LOGICAL_TARGET = "LOGICAL_TARGET"
    LOGICAL_EARLY = "LOGICAL_EARLY"
    TRANSMONS = "TRANSMONS"


class OQCBackendNames(StrEnum):
    """
    OQC backend names which Classiq Supports running on.
    """

    LUCY = "Lucy"


EXACT_SIMULATORS = {
    IonqBackendNames.SIMULATOR,
    AzureQuantumBackendNames.IONQ_SIMULATOR,
    AzureQuantumBackendNames.MICROSOFT_FULLSTATE_SIMULATOR,
    AmazonBraketBackendNames.AMAZON_BRAKET_SV1,
    AmazonBraketBackendNames.AMAZON_BRAKET_TN1,
    AmazonBraketBackendNames.AMAZON_BRAKET_DM1,
    *ClassiqSimulatorBackendNames,
    *IntelBackendNames,
    *ClassiqNvidiaBackendNames,
}

AllIBMQBackendNames = IBMQHardwareNames

AllBackendsNameByVendor = Union[
    AllIBMQBackendNames,
    AzureQuantumBackendNames,
    AmazonBraketBackendNames,
    IonqBackendNames,
    IntelBackendNames,
    ClassiqNvidiaBackendNames,
    AliceBobBackendNames,
    OQCBackendNames,
]

AllBackendsNameEnums = [
    IBMQHardwareNames,
    AzureQuantumBackendNames,
    AmazonBraketBackendNames,
    IonqBackendNames,
    AliceBobBackendNames,
    IntelBackendNames,
    ClassiqNvidiaBackendNames,
    OQCBackendNames,
]
