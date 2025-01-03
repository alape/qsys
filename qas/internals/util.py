from enum import Enum
from typing import Self


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
