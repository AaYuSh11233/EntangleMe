from typing import Union


def s(items: Union[list, int]) -> str:
    if isinstance(items, list):
        items = len(items)
    return "" if items == 1 else "s"


def are(items: list) -> str:
    return "is" if len(items) == 1 else "are"


def they(items: list) -> str:
    return "it" if len(items) == 1 else "they"


def readable_list(items: list, quote: bool = False) -> str:
    if quote:
        items = [repr(str(item)) for item in items]
    if len(items) == 1:
        return str(items[0])
    return f"{', '.join(items[:-1])}{',' if len(items) > 2 else ''} and {items[-1]}"
