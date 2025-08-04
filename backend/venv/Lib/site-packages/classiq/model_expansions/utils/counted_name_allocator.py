from collections import Counter


class CountedNameAllocator:
    def __init__(self) -> None:
        self._count: Counter[str] = Counter()

    def allocate(self, prefix: str) -> str:
        allocated = f"{prefix}_{self._count[prefix]}"
        self._count[prefix] += 1
        return allocated
