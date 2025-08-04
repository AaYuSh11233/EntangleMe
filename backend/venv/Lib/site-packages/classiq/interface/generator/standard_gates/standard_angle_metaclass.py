from typing import Any

import pydantic

from classiq.interface.generator.function_params import FunctionParamsNumericParameter

PydanticMetaClass: Any = type(pydantic.BaseModel)


# This metaclass helps define which angles should be used in each angled gate as can be seen in their implementations
class MyMetaAngledClass(type):
    def __new__(cls, name: str, bases: tuple, namespace: dict, **kwargs: Any) -> type:
        a_totally_new_namespace = cls._create_new_namespace(namespace, **kwargs)
        return type.__new__(cls, name, bases, a_totally_new_namespace)

    @staticmethod
    def _create_new_namespace(namespace: dict, **kwargs: Any) -> dict:
        angles = kwargs.get("angles", [])
        annotations = {angle: FunctionParamsNumericParameter for angle in angles}
        original_annotations = namespace.get("__annotations__", {})
        return {
            **namespace,
            **{"__annotations__": {**original_annotations, **annotations}},
        }


class MyMetaAngledClassModel(PydanticMetaClass, MyMetaAngledClass):
    def __new__(
        cls, name: str, bases: tuple, namespace: dict, **kwargs: Any
    ) -> PydanticMetaClass:
        # First, populate the namespace (specifically, "__annotations__") according to `MyMetaAngledClass` with the angles defined
        namespace = MyMetaAngledClass._create_new_namespace(namespace, **kwargs)

        # Clean `kwargs` afterwards so that it won't pass again to the final class
        if "angles" in kwargs:
            kwargs.pop("angles")

        # Next, continue with pydantic's flow
        return PydanticMetaClass.__new__(cls, name, bases, namespace, **kwargs)
