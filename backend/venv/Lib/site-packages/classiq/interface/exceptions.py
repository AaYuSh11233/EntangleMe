import logging
from collections.abc import Iterable
from typing import Optional

_logger = logging.getLogger(__name__)

CLASSIQ_SLACK_COMMUNITY_LINK = (
    "\nIf you need further assistance, please reach out on our Community Slack channel "
    "at: https://short.classiq.io/join-slack or open a support ticket at: "
    "https://classiq-community.freshdesk.com/support/tickets/new"
)


class ClassiqError(Exception):
    def __init__(self, message: str) -> None:
        self._raw_message = message
        if CLASSIQ_SLACK_COMMUNITY_LINK not in message:
            message = message + CLASSIQ_SLACK_COMMUNITY_LINK
        super().__init__(message)

    @property
    def raw_message(self) -> str:
        return self._raw_message


class ClassiqExecutionError(ClassiqError):
    pass


class ClassiqMissingOutputFormatError(ClassiqError):
    def __init__(self, missing_formats: list[str]) -> None:
        msg = (
            f"Cannot create program because output format is missing. "
            f"Expected one of the following formats: {missing_formats}"
        )
        super().__init__(message=msg)


class ClassiqCombinatorialOptimizationError(ClassiqError):
    pass


class ClassiqOracleError(ClassiqError):
    pass


class ClassiqAnalyzerError(ClassiqError):
    pass


class ClassiqAnalyzerVisualizationError(ClassiqError):
    pass


class ClassiqAPIError(ClassiqError):
    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        self.status_code = status_code
        super().__init__(message)


class ClassiqVersionError(ClassiqError):
    pass


class ClassiqValueError(ClassiqError, ValueError):
    pass


class ClassiqArithmeticError(ClassiqValueError):
    pass


class ClassiqIndexError(ClassiqError, IndexError):
    pass


class ClassiqWiringError(ClassiqValueError):
    pass


class ClassiqControlError(ClassiqError):
    def __init__(self) -> None:
        message = "Repeated control names, please rename the control states"
        super().__init__(message=message)


class ClassiqQRegError(ClassiqValueError):
    pass


class ClassiqQFuncError(ClassiqValueError):
    pass


class ClassiqQSVMError(ClassiqValueError):
    pass


class ClassiqQNNError(ClassiqValueError):
    pass


class ClassiqTorchError(ClassiqQNNError):
    pass


class ClassiqChemistryError(ClassiqError):
    pass


class ClassiqAuthenticationError(ClassiqError):
    pass


class ClassiqExpiredTokenError(ClassiqAuthenticationError):
    pass


class ClassiqFileNotFoundError(FileNotFoundError):
    pass


class ClassiqStateInitializationError(ClassiqError):
    pass


class ClassiqPasswordManagerSelectionError(ClassiqError):
    pass


class ClassiqMismatchIOsError(ClassiqError):
    pass


class ClassiqNotImplementedError(ClassiqError, NotImplementedError):
    pass


class ClassiqCombOptError(ClassiqError):
    pass


class ClassiqCombOptNoSolutionError(ClassiqError):

    def __init__(self) -> None:
        super().__init__("There is no valid solution for this optimization problem.")


class ClassiqCombOptTrivialProblemError(ClassiqError):

    def __init__(self, solution: list[int]) -> None:
        super().__init__(
            message=f"The problem doesn't have free decision variables. "
            f"The trivial solution is {solution}."
        )


class ClassiqCombOptInvalidEncodingTypeError(ClassiqError):

    def __init__(self, encoding_type: str, valid_types: Iterable[str]) -> None:
        super().__init__(
            f"Invalid variable encoding type {encoding_type}. "
            f"The available encoding types are {list(valid_types)}"
        )


class ClassiqNonNumericCoefficientInPauliError(ClassiqError):
    pass


class ClassiqCombOptNotSupportedProblemError(ClassiqCombOptError):
    pass


class ClassiqExecutorInvalidHamiltonianError(ClassiqCombOptError):

    def __init__(self) -> None:
        super().__init__("Invalid hamiltonian")


class ClassiqDeprecationWarning(FutureWarning):
    pass


class ClassiqExpansionError(ClassiqError):
    pass


class ClassiqInternalError(ClassiqError):
    def __init__(self, message: Optional[str] = None) -> None:
        final_message = "Internal error occurred. Please contact Classiq support."
        if message is not None:
            final_message += f"\nError: {message}"
        super().__init__(final_message)


class ClassiqInternalExpansionError(ClassiqInternalError):
    pass
