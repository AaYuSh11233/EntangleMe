from __future__ import annotations

import warnings
from collections.abc import Iterable
from typing import Any, Optional, Union

import pydantic
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from classiq.interface.backend import pydantic_backend
from classiq.interface.backend.quantum_backend_providers import (
    EXACT_SIMULATORS,
    AliceBobBackendNames,
    AmazonBraketBackendNames,
    AzureQuantumBackendNames,
    ClassiqNvidiaBackendNames,
    ClassiqSimulatorBackendNames,
    IntelBackendNames,
    IonqBackendNames,
    OQCBackendNames,
    ProviderTypeVendor,
    ProviderVendor,
)
from classiq.interface.exceptions import ClassiqDeprecationWarning
from classiq.interface.hardware import Provider


class BackendPreferences(BaseModel):
    """
    Preferences for the execution of the quantum program.

    Attributes:
        backend_service_provider (str): Provider company or cloud for the requested backend.
        backend_name (str): Name of the requested backend or target.
    """

    backend_service_provider: ProviderVendor = pydantic.Field(
        ..., description="Provider company or cloud for the requested backend."
    )
    backend_name: str = pydantic.Field(
        ..., description="Name of the requested backend or target."
    )

    @property
    def hw_provider(self) -> Provider:
        return Provider(self.backend_service_provider)

    @classmethod
    def batch_preferences(
        cls, *, backend_names: Iterable[str], **kwargs: Any
    ) -> list[BackendPreferences]:
        return [cls(backend_name=name, **kwargs) for name in backend_names]

    def is_nvidia_backend(self) -> bool:
        return False


class AliceBobBackendPreferences(BackendPreferences):
    """
    Backend preferences specific to Alice&Bob for quantum computing tasks.

    This class includes configuration options for setting up a backend using Alice&Bob's quantum hardware.
    It extends the base `BackendPreferences` class and provides additional parameters required for working
    with Alice&Bob's cat qubits, including settings for photon dissipation rates, repetition code distance,
    and the average number of photons.

    Attributes:
        backend_service_provider (ProviderTypeVendor.ALICE_BOB):
            The service provider for the backend, which is Alice&Bob.

        distance (Optional[int]):
            The number of times information is duplicated in the repetition code.
            - **Tooltip**: Phase-flip probability decreases exponentially with this parameter, bit-flip probability increases linearly.
            - **Supported Values**: 3 to 300, though practical values are usually lower than 30.
            - **Default**: None.

        kappa_1 (Optional[float]):
            The rate at which the cat qubit loses one photon, creating a bit-flip.
            - **Tooltip**: Lower values mean lower error rates.
            - **Supported Values**: 10 to 10^5. Current hardware is at ~10^3.
            - **Default**: None.

        kappa_2 (Optional[float]):
            The rate at which the cat qubit is stabilized using two-photon dissipation.
            - **Tooltip**: Higher values mean lower error rates.
            - **Supported Values**: 100 to 10^9. Current hardware is at ~10^5.
            - **Default**: None.

        average_nb_photons (Optional[float]):
            The average number of photons.
            - **Tooltip**: Bit-flip probability decreases exponentially with this parameter, phase-flip probability increases linearly.
            - **Supported Values**: 4 to 10^5, though practical values are usually lower than 30.
            - **Default**: None.

        api_key (str):
            The API key required to access Alice&Bob's quantum hardware.
            - **Required**: Yes.

    For more details, refer to the [Alice&Bob Backend Documentation](https://docs.classiq.io/latest/reference-manual/executor/cloud-providers/alice-and-bob-backends/).
    """

    backend_service_provider: ProviderTypeVendor.ALICE_BOB = pydantic.Field(
        default=ProviderVendor.ALICE_AND_BOB
    )
    distance: Optional[int] = pydantic.Field(
        default=None, description="Repetition code distance"
    )
    kappa_1: Optional[float] = pydantic.Field(
        default=None, description="One-photon dissipation rate (Hz)"
    )
    kappa_2: Optional[float] = pydantic.Field(
        default=None, description="Two-photon dissipation rate (Hz)"
    )
    average_nb_photons: Optional[float] = pydantic.Field(
        default=None, description="Average number of photons"
    )
    api_key: Optional[pydantic_backend.PydanticAliceBobApiKeyType] = pydantic.Field(
        default=None, description="AliceBob API key"
    )

    @property
    def parameters(self) -> dict[str, Any]:
        parameters = {
            "distance": self.distance,
            "kappa1": self.kappa_1,
            "kappa2": self.kappa_2,
            "averageNbPhotons": self.average_nb_photons,
        }
        return {k: v for k, v in parameters.items() if v is not None}

    @pydantic.field_validator("api_key", mode="after")
    @classmethod
    def _validate_api_key(cls, api_key: Optional[str]) -> Optional[str]:
        if api_key is not None:
            warnings.warn(
                "API key is no longer required for Alice&Bob backends.",
                ClassiqDeprecationWarning,
                stacklevel=2,
            )
        return api_key


class ClassiqBackendPreferences(BackendPreferences):
    """
    Represents backend preferences specific to Classiq quantum computing targets.

    This class is used to configure the backend options for executing quantum circuits on Classiq's platform.
    The relevant backend names for Classiq targets are specified in `ClassiqSimulatorBackendNames` & `ClassiqNvidiaBackendNames`.

    For more details, refer to the [Classiq Backend Documentation](https://docs.classiq.io/latest/reference-manual/executor/cloud-providers/classiq-backends/).
    """

    backend_service_provider: ProviderTypeVendor.CLASSIQ = pydantic.Field(
        default=ProviderVendor.CLASSIQ
    )

    def is_nvidia_backend(self) -> bool:
        return self.backend_name in list(ClassiqNvidiaBackendNames)


class AwsBackendPreferences(BackendPreferences):
    """
    AWS-specific backend preferences for quantum computing tasks using Amazon Braket.

    This class contains configuration options specific to Amazon Braket, including the AWS role
    ARN, S3 bucket details, and the folder path within the S3 bucket. It extends the base
    `BackendPreferences` class to provide additional properties required for interaction with
    Amazon Braket.

    Attributes:
        backend_service_provider (ProviderTypeVendor.AMAZON_BRAKET):
            The service provider for the backend, which is Amazon Braket.

        aws_role_arn (pydantic_backend.PydanticAwsRoleArn):
            The Amazon Resource Name (ARN) of the role that will be assumed for execution
            on your Braket account. This is a required field and should be provided to allow
            secure and authorized access to AWS resources.

        s3_bucket_name (str):
            The name of the S3 bucket where results and other related data will be stored.
            This field should contain a valid S3 bucket name under your AWS account.

        s3_folder (pydantic_backend.PydanticS3BucketKey):
            The folder path within the specified S3 bucket. This allows for organizing
            results and data under a specific directory within the S3 bucket.


    For more details, refer to:
    [AwsBackendPreferences examples](https://docs.classiq.io/latest/reference-manual/executor/cloud-providers/amazon-backends/?h=awsbackend#usage)
    """

    backend_service_provider: ProviderTypeVendor.AMAZON_BRAKET = pydantic.Field(
        default=ProviderVendor.AMAZON_BRAKET
    )
    aws_role_arn: Optional[str] = pydantic.Field(
        default=None,
        description="ARN of the role to be assumed for execution on your Braket account.",
    )
    s3_bucket_name: Optional[str] = pydantic.Field(
        default=None, description="S3 Bucket Name"
    )
    s3_folder: Optional[str] = pydantic.Field(
        default=None, description="S3 Folder Path Within The S3 Bucket"
    )
    run_through_classiq: bool = pydantic.Field(
        default=False,
        description="Run through Classiq's credentials while using user's allocated budget.",
    )


class IBMBackendPreferences(BackendPreferences):
    """
    Represents the backend preferences specific to IBM Quantum services.

    Inherits from `BackendPreferences` and adds additional fields and validations
    specific to IBM Quantum backends.

    Attributes:
        backend_service_provider (ProviderTypeVendor.IBM_CLOUD): Indicates the backend service provider as IBM Cloud.
        access_token (Optional[str]): The IBM Cloud access token to be used with IBM Quantum hosted backends. Defaults to `None`.
        channel (str): Channel to use for IBM cloud backends. Defaults to `"ibm_cloud"`.
        instance_crn (str): The IBM Cloud instance CRN (Cloud Resource Name) for the IBM Quantum service.
        run_through_classiq (bool): Run through Classiq's credentials. Defaults to `False`.

    See examples in the [IBM Quantum Backend Documentation](https://docs.classiq.io/latest/reference-manual/executor/cloud-providers/ibm-backends/?h=).
    """

    backend_service_provider: ProviderTypeVendor.IBM_CLOUD = pydantic.Field(
        default=ProviderVendor.IBM_QUANTUM
    )
    access_token: Optional[str] = pydantic.Field(
        default=None,
        description="IBM Cloud access token to be used"
        " with IBM Quantum hosted backends",
    )
    channel: Optional[str] = pydantic.Field(
        default=None, description="Channel to use for IBM cloud backends."
    )
    instance_crn: Optional[str] = pydantic.Field(
        default=None, description="IBM Cloud instance CRN."
    )
    run_through_classiq: bool = pydantic.Field(
        default=False,
        description="Run through Classiq's credentials",
    )


class AzureCredential(BaseSettings):
    """
    Represents the credentials and configuration required to authenticate with Azure services.

    Attributes:
        tenant_id (str): Azure Tenant ID used to identify the directory in which the application is registered.
        client_id (str): Azure Client ID, also known as the application ID, which is used to authenticate the application.
        client_secret (str): Azure Client Secret associated with the application, used for authentication.
        resource_id (pydantic_backend.PydanticAzureResourceIDType): Azure Resource ID, including the subscription ID,
            resource group, and workspace, typically used for personal resources.
    """

    tenant_id: str = pydantic.Field(description="Azure Tenant ID")
    client_id: str = pydantic.Field(description="Azure Client ID")
    client_secret: str = pydantic.Field(description="Azure Client Secret")
    resource_id: pydantic_backend.PydanticAzureResourceIDType = pydantic.Field(
        description="Azure Resource ID (including Azure subscription ID, resource "
        "group and workspace), for personal resource",
    )
    model_config = SettingsConfigDict(
        title="Azure Service Principal Credential",
        env_prefix="AZURE_",
        case_sensitive=False,
        extra="allow",
    )

    def __init__(self, **data: Any) -> None:
        initial_data = {
            field: data[field] for field in data if field in self.model_fields
        }
        super().__init__(**data)
        for field, value in initial_data.items():
            setattr(self, field, value)


class AzureBackendPreferences(BackendPreferences):
    """
    This class inherits from BackendPreferences.
    This is where you specify Azure Quantum preferences.
    See usage in the [Azure Backend Documentation](https://docs.classiq.io/latest/reference-manual/executor/cloud-providers/azure-backends/).

    Attributes:
        location (str): Azure personal resource region. Defaults to `"East US"`.
        credentials (Optional[AzureCredential]): The service principal credential to access personal quantum workspace. Defaults to `None`.
        ionq_error_mitigation_flag (Optional[bool]): Error mitigation configuration upon running on IonQ through Azure. Defaults to `False`.


    """

    backend_service_provider: ProviderTypeVendor.AZURE_QUANTUM = pydantic.Field(
        default=ProviderVendor.AZURE_QUANTUM
    )

    location: str = pydantic.Field(
        default="East US", description="Azure personal resource region"
    )

    credentials: Optional[AzureCredential] = pydantic.Field(
        default=None,
        description="The service principal credential to access personal quantum workspace",
    )

    ionq_error_mitigation_flag: Optional[bool] = pydantic.Field(
        default=False,
        description="Error mitigation configuration upon running on IonQ through Azure.",
    )

    @property
    def run_through_classiq(self) -> bool:
        """

        Returns: `True` if there are no Azure Credentials.
        Therefore you will be running through Classiq's credentials.

        """
        return self.credentials is None


class IonqBackendPreferences(BackendPreferences):
    """
    Represents the backend preferences specific to IonQ services.

    Inherits from `BackendPreferences` and adds additional fields and configurations
    specific to IonQ backends

    Attributes:
        backend_service_provider (ProviderTypeVendor.IONQ): Indicates the backend service provider as IonQ.
        api_key (PydanticIonQApiKeyType): The IonQ API key required for accessing IonQ's quantum computing services.
        error_mitigation (bool): A configuration option to enable or disable error mitigation during execution. Defaults to `False`.
        run_through_classiq (bool): Running through Classiq's credentials while using user's allocated budget.

    See examples in the [IonQ Backend Documentation](https://docs.classiq.io/latest/reference-manual/executor/cloud-providers/ionq-backends/?h=).
    """

    backend_service_provider: ProviderTypeVendor.IONQ = pydantic.Field(
        default=ProviderVendor.IONQ
    )
    api_key: Optional[pydantic_backend.PydanticIonQApiKeyType] = pydantic.Field(
        default=None, description="IonQ API key"
    )
    error_mitigation: bool = pydantic.Field(
        default=False,
        description="Error mitigation configuration.",
    )
    run_through_classiq: bool = pydantic.Field(
        default=False,
        description="Running through Classiq's credentials while using user's allocated budget.",
    )


class GCPBackendPreferences(BackendPreferences):
    """
    Represents the backend preferences specific to Google Cloud Platform (GCP) services.

    Inherits from `BackendPreferences` and sets the backend service provider to Google.

    Attributes:
        backend_service_provider (ProviderTypeVendor.GOOGLE): Indicates the backend service provider as Google,
        specifically for quantum computing services on Google Cloud Platform (GCP).

    See examples in the [Google Cloud Backend Documentation](https://docs.classiq.io/latest/reference-manual/executor/cloud-providers/google-backends/?h=).
    """

    backend_service_provider: ProviderTypeVendor.GOOGLE = pydantic.Field(
        default=ProviderVendor.GOOGLE
    )

    def is_nvidia_backend(self) -> bool:
        return True


class OQCBackendPreferences(BackendPreferences):
    """

    This class inherits from `BackendPreferences`.
    This is where you specify OQC preferences.

    Attributes:
        username (str): OQC username
        password (str): OQC password
    """

    backend_service_provider: ProviderTypeVendor.OQC = pydantic.Field(
        default=ProviderVendor.OQC
    )
    username: str = pydantic.Field(description="OQC username")
    password: str = pydantic.Field(description="OQC password")


class IntelBackendPreferences(BackendPreferences):
    """
    Represents backend preferences specific to Classiq quantum computing targets.

    This class is used to configure the backend options for executing quantum circuits on Classiq's platform.
    The relevant backend names for Classiq targets are specified in `ClassiqSimulatorBackendNames` & `ClassiqNvidiaBackendNames`.

    For more details, refer to the [Classiq Backend Documentation](https://docs.classiq.io/latest/reference-manual/executor/cloud-providers/classiq-backends/).
    """

    backend_service_provider: ProviderTypeVendor.INTEL = pydantic.Field(
        default=ProviderVendor.INTEL
    )


class AQTBackendPreferences(BackendPreferences):
    """
    NOTE: This is a work in progress and is subject to change.

    Represents the backend preferences specific to AQT (Alpine Quantum Technologies).

    Attributes:
        api_key: The API key required to access AQT's quantum computing services.
        workspace: The AQT workspace where the simulator/hardware is located.
    """

    backend_service_provider: ProviderTypeVendor.AQT = pydantic.Field(
        default=ProviderVendor.AQT
    )
    api_key: str = pydantic.Field(description="AQT API key")
    workspace: str = pydantic.Field(description="AQT workspace")


class IQCCBackendPreferences(BackendPreferences):
    """
    NOTE: This is a work in progress and is subject to change.

    Represents the backend preferences specific to IQCC (Israeli Quantum Computing
    Center).

    Attributes:
        auth_token: The authorization token generated by calling `generate_iqcc_token`.
        target_id: The target ID of the login node.
        target_scope_id: The scope ID of the specified target.
        ssh_user_name: The user name to use when connecting to the SSH server on the login node.
        ssh_key: The private key to use when connecting to the SSH server on the login node.
        slurm_account: The account to use when initiating SLURM jobs.
    """

    backend_service_provider: ProviderTypeVendor.IQCC = pydantic.Field(
        default=ProviderVendor.IQCC
    )
    auth_token: str
    target_id: str
    target_scope_id: str
    ssh_user_name: str
    ssh_key: str
    slurm_account: str


class CINECABackendPreferences(BackendPreferences):
    """
    Represents the backend preferences specific to CINECA.

    Attributes:
        ssh_username: The username to use when connecting to the SSH server on the login node.
        ssh_private_key_path: The path to the ssh private key on local machine.
    """

    backend_service_provider: ProviderTypeVendor.CINECA = pydantic.Field(
        default=ProviderVendor.CINECA
    )

    ssh_username: str = pydantic.Field(
        description="Username to use when connecting to the SSH server on the login node."
    )
    ssh_private_key_path: str = pydantic.Field(
        description="Path of private key file on local machine to use when connecting to the SSH server on the login node."
    )


def is_exact_simulator(backend_preferences: BackendPreferences) -> bool:
    return backend_preferences.backend_name in EXACT_SIMULATORS


def default_backend_preferences(
    backend_name: str = ClassiqSimulatorBackendNames.SIMULATOR,
) -> BackendPreferences:
    return ClassiqBackendPreferences(backend_name=backend_name)


def backend_preferences_field(
    backend_name: str = ClassiqSimulatorBackendNames.SIMULATOR,
) -> Any:
    return pydantic.Field(
        default_factory=lambda: default_backend_preferences(backend_name),
        description="Preferences for the requested backend to run the quantum circuit.",
        discriminator="backend_service_provider",
    )


BackendPreferencesTypes = Union[
    AzureBackendPreferences,
    ClassiqBackendPreferences,
    IBMBackendPreferences,
    AwsBackendPreferences,
    IonqBackendPreferences,
    GCPBackendPreferences,
    AliceBobBackendPreferences,
    OQCBackendPreferences,
    IntelBackendPreferences,
    AQTBackendPreferences,
    IQCCBackendPreferences,
    CINECABackendPreferences,
]

__all__ = [
    "AQTBackendPreferences",
    "AliceBobBackendNames",
    "AliceBobBackendPreferences",
    "AmazonBraketBackendNames",
    "AwsBackendPreferences",
    "AzureBackendPreferences",
    "AzureCredential",
    "AzureQuantumBackendNames",
    "ClassiqBackendPreferences",
    "ClassiqNvidiaBackendNames",
    "ClassiqSimulatorBackendNames",
    "GCPBackendPreferences",
    "IBMBackendPreferences",
    "IQCCBackendPreferences",
    "IntelBackendNames",
    "IntelBackendPreferences",
    "IonqBackendNames",
    "IonqBackendPreferences",
    "OQCBackendNames",
    "OQCBackendPreferences",
]
