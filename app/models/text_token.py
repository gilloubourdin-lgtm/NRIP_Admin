from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TextToken:
    """
    Unité lexicale extraite d'un texte avec sa position exacte.

    Les positions suivent la convention Python :
    - start est inclusif ;
    - end est exclusif.
    """

    value: str
    start: int
    end: int

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("TextToken.value ne peut pas être vide.")

        if self.start < 0:
            raise ValueError(
                "TextToken.start doit être supérieur ou égal à 0."
            )

        if self.end <= self.start:
            raise ValueError(
                "TextToken.end doit être strictement supérieur à start."
            )

        if self.end - self.start != len(self.value):
            raise ValueError(
                "La longueur du token doit correspondre à son intervalle."
            )

    @property
    def length(self) -> int:
        return self.end - self.start

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)