from typing import Optional

from classiq.interface.generator.expressions.handle_identifier import HandleIdentifier
from classiq.interface.generator.functions.classical_type import QmodPyObject


class HandleTable:
    _handle_map: dict[HandleIdentifier, QmodPyObject] = {}

    @classmethod
    def get_handle_object(cls, hid: HandleIdentifier) -> Optional[QmodPyObject]:
        return cls._handle_map.get(hid)

    @classmethod
    def set_handle_object(cls, qmod_object: QmodPyObject) -> HandleIdentifier:
        hid = HandleIdentifier(id(qmod_object))
        cls._handle_map[hid] = qmod_object
        return hid
