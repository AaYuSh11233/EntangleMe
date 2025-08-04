from typing import TYPE_CHECKING, Any, Union

from classiq.interface.generator.complex_type import Complex

if TYPE_CHECKING:
    from typing_extensions import TypeAlias
else:
    TypeAlias = Any

ParameterType: TypeAlias = str
ParameterFloatType: TypeAlias = Union[float, ParameterType]
ParameterComplexType: TypeAlias = Union[complex, ParameterType]
PydanticParameterComplexType: TypeAlias = Union[Complex, ParameterType]
