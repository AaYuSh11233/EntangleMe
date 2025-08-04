import sys
from abc import ABC, abstractmethod
from typing import (  # type: ignore[attr-defined]
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Optional,
    Union,
    _GenericAlias,
)

from typing_extensions import ParamSpec

from classiq.interface.model.quantum_function_call import QuantumFunctionCall
from classiq.interface.model.quantum_function_declaration import (
    AnonQuantumFunctionDeclaration,
)
from classiq.interface.model.quantum_statement import QuantumStatement
from classiq.interface.model.quantum_type import QuantumType
from classiq.interface.source_reference import SourceReference

from classiq.qmod.cparam import CInt
from classiq.qmod.utilities import get_source_ref, suppress_return_value

if TYPE_CHECKING:
    from classiq.qmod.quantum_expandable import QTerminalCallable

P = ParamSpec("P")


class QExpandableInterface(ABC):
    @abstractmethod
    def append_statement_to_body(self, stmt: QuantumStatement) -> None:
        raise NotImplementedError()

    @abstractmethod
    def add_local_handle(
        self,
        name: str,
        qtype: QuantumType,
        source_ref: Optional[SourceReference] = None,
    ) -> None:
        raise NotImplementedError()


class QCallable(Generic[P], ABC):
    CURRENT_EXPANDABLE: ClassVar[Optional[QExpandableInterface]] = None
    FRAME_DEPTH = 1

    @suppress_return_value
    def __call__(self, *args: Any, **kwargs: Any) -> None:
        assert QCallable.CURRENT_EXPANDABLE is not None
        source_ref = get_source_ref(sys._getframe(self.FRAME_DEPTH))
        QCallable.CURRENT_EXPANDABLE.append_statement_to_body(
            self.create_quantum_function_call(source_ref, *args, **kwargs)
        )
        return

    @property
    @abstractmethod
    def func_decl(self) -> AnonQuantumFunctionDeclaration:
        raise NotImplementedError

    # Support comma-separated generic args in older Python versions
    if sys.version_info[0:2] < (3, 10):

        def __class_getitem__(cls, args) -> _GenericAlias:
            return _GenericAlias(cls, args)

    @abstractmethod
    def create_quantum_function_call(
        self, source_ref_: SourceReference, *args: Any, **kwargs: Any
    ) -> QuantumFunctionCall:
        raise NotImplementedError()


class QCallableList(QCallable, Generic[P], ABC):
    if TYPE_CHECKING:

        @property
        def len(self) -> int: ...

        def __getitem__(self, key: Union[slice, int, CInt]) -> "QTerminalCallable":
            raise NotImplementedError()
