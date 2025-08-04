from collections.abc import Mapping
from typing import Any

from classiq.interface.generator.expressions.proxies.classical.qmod_struct_instance import (
    QmodStructInstance,
)

QmodPyStruct = Mapping[str, Any]


def qmod_value_to_dict(qmod_value: Any) -> Any:
    if isinstance(qmod_value, QmodStructInstance):
        return {
            field_name: qmod_value_to_dict(field_value)
            for field_name, field_value in qmod_value.fields.items()
        }
    if isinstance(qmod_value, list):
        return [qmod_value_to_dict(item) for item in qmod_value]
    return qmod_value
