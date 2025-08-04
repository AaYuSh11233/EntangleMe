from classiq.interface.exceptions import ClassiqInternalExpansionError
from classiq.interface.generator.expressions.evaluated_expression import (
    EvaluatedExpression,
)
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.expressions.proxies.classical.classical_array_proxy import (
    ClassicalArrayProxy,
    ClassicalTupleProxy,
)
from classiq.interface.generator.expressions.proxies.classical.classical_proxy import (
    ClassicalProxy,
)
from classiq.interface.generator.expressions.proxies.classical.classical_scalar_proxy import (
    ClassicalScalarProxy,
)
from classiq.interface.generator.expressions.proxies.classical.classical_struct_proxy import (
    ClassicalStructProxy,
)
from classiq.interface.generator.functions.classical_type import (
    ClassicalArray,
    ClassicalTuple,
    ClassicalType,
)
from classiq.interface.generator.functions.type_name import Struct


def get_proxy_type(proxy: ClassicalProxy) -> ClassicalType:
    if isinstance(proxy, ClassicalScalarProxy):
        return proxy._classical_type
    if isinstance(proxy, ClassicalArrayProxy):
        if not isinstance(proxy.length, int):
            return ClassicalArray(element_type=proxy._element_type)
        length = Expression(expr=str(proxy.length))
        length._evaluated_expr = EvaluatedExpression(value=proxy.length)
        return ClassicalArray(element_type=proxy._element_type, length=length)
    if isinstance(proxy, ClassicalTupleProxy):
        return ClassicalTuple(element_types=proxy._element_types)
    if isinstance(proxy, ClassicalStructProxy):
        classical_type = Struct(name=proxy._decl.name)
        classical_type.set_classical_struct_decl(proxy._decl)
        return classical_type
    raise ClassiqInternalExpansionError(
        f"Unrecognized classical proxy {type(proxy).__name__}"
    )
