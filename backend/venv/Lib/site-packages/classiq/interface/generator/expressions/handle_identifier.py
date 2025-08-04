import dataclasses


@dataclasses.dataclass(frozen=True)
class HandleIdentifier:
    id: int
