from typing import Any


class DotDict(dict):
    def __getattr__(self, key: str) -> Any:
        return super().get(key)

    def __setattr__(self, key: str, value: Any) -> None:
        super().__setitem__(key, value)

    def __delattr__(self, key: str) -> None:
        super().__delitem__(key)


class LenList(list):
    @property
    def len(self) -> int:
        return len(self)

    def __getitem__(self, item: Any) -> Any:
        res = super().__getitem__(item)
        if isinstance(item, slice):
            res = type(self)(res)
        return res


def get_sdk_compatible_python_object(obj: Any) -> Any:
    if isinstance(obj, list):
        return LenList([get_sdk_compatible_python_object(item) for item in obj])
    if isinstance(obj, dict):
        return DotDict({k: get_sdk_compatible_python_object(v) for k, v in obj.items()})
    return obj
