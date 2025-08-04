import abc
from collections.abc import Sequence

from pydantic import ConfigDict

from classiq.interface.model.classical_parameter_declaration import (
    AnonClassicalParameterDeclaration,
)
from classiq.interface.model.parameter import Parameter


class FunctionDeclaration(Parameter, abc.ABC):
    """
    Facilitates the creation of a common function interface object.
    """

    @property
    @abc.abstractmethod
    def param_decls(self) -> Sequence["AnonClassicalParameterDeclaration"]:
        pass

    model_config = ConfigDict(extra="forbid")


FunctionDeclaration.model_rebuild()
