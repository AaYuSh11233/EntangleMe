import datetime
from typing import TYPE_CHECKING, Annotated, Optional

import pydantic

from classiq.interface.enum_utils import StrEnum

QueueTime = Annotated[
    Optional[datetime.timedelta],
    pydantic.PlainSerializer(
        lambda _timedelta: (
            _timedelta.total_seconds() if _timedelta is not None else None
        ),
        return_type=Optional[float],
    ),
]


class Provider(StrEnum):
    """
    This class defines all Providers that Classiq supports.
    This is mainly used in backend_preferences when specifying where do we want to execute the defined model.
    """

    IBM_QUANTUM = "IBM Quantum"
    AZURE_QUANTUM = "Azure Quantum"
    AMAZON_BRAKET = "Amazon Braket"
    IONQ = "IonQ"
    CLASSIQ = "Classiq"
    GOOGLE = "Google"
    ALICE_AND_BOB = "Alice & Bob"
    OQC = "OQC"
    INTEL = "Intel"
    AQT = "AQT"
    IQCC = "IQCC"
    CINECA = "CINECA"

    @property
    def id(self) -> "ProviderIDEnum":
        return self.value.replace(" ", "-").lower()  # type: ignore[return-value]


ProviderIDEnum = StrEnum("ProviderIDEnum", {p.id: p.id for p in Provider})  # type: ignore[misc]


class AvailabilityStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"

    @property
    def is_available(self) -> bool:
        return self == self.AVAILABLE


class DeviceType(StrEnum):
    SIMULATOR = "simulator"
    HARDWARE = "hardware"
    STATEVECTOR = "state_vector_simulator"

    @property
    def is_simulator(self) -> bool:
        return self != self.HARDWARE


class HardwareStatus(pydantic.BaseModel):
    last_update_time: datetime.datetime = pydantic.Field(
        default_factory=lambda: datetime.datetime.now(tz=datetime.UTC)
    )
    availability: AvailabilityStatus
    queue_time: QueueTime = pydantic.Field(
        default=None,
        description="The estimated queue time for the hardware in seconds.",
    )
    pending_jobs: Optional[int] = None


if TYPE_CHECKING:
    ConnectivityMapEntry = tuple[int, int]
else:
    ConnectivityMapEntry = list[int]


class HardwareInformation(pydantic.BaseModel):
    provider: Provider
    vendor: str
    name: str
    display_name: str
    device_type: DeviceType
    number_of_qubits: int
    connectivity_map: Optional[list[ConnectivityMapEntry]] = None
    basis_gates: list[str]
    status: HardwareStatus

    def is_simulator(self) -> bool:
        return self.device_type != DeviceType.HARDWARE
