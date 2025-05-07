from enum import Enum
from typing import Self, TypeVar


class IndexableEnum(Enum):
    """Trait class that enables its Enum descendants to be indexed by string keys."""

    @classmethod
    def from_string(cls, key: str) -> Self:
        """Returns value of itself that matches by name the string provided (character case is ignored)."""
        for val in cls:
            if val.name.lower() == key.lower():
                return val

        raise KeyError(f"Value {key} is not present in {cls.__name__} enum")

    @classmethod
    def indices(cls) -> list[str]:
        """Returns a list of all string indices of itself."""
        return [v.name for v in cls]


T = TypeVar("T")


def slice_by_chunks(e: T, chunk_len: int) -> list[T]:
    """Splits `e` into multiple chunks, each `chunk_len` in length or less (final chunk)."""
    return [e[i:i + chunk_len] for i in range(0, len(e), chunk_len)]
