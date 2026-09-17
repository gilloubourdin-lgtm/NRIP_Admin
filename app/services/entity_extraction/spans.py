from __future__ import annotations

from dataclasses import dataclass

from app.models.text_token import TextToken


@dataclass(frozen=True, slots=True)
class TextSpan:
    """
    Portion continue du texte construite à partir d'un ou plusieurs tokens.

    Les positions suivent la convention Python :
    - start inclusif ;
    - end exclusif.
    """

    value: str
    start: int
    end: int
    token_count: int

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("TextSpan.value ne peut pas être vide.")

        if self.start < 0:
            raise ValueError(
                "TextSpan.start doit être supérieur ou égal à 0."
            )

        if self.end <= self.start:
            raise ValueError(
                "TextSpan.end doit être strictement supérieur à start."
            )

        if self.token_count < 1:
            raise ValueError(
                "TextSpan.token_count doit être supérieur ou égal à 1."
            )

    @property
    def length(self) -> int:
        return self.end - self.start


class SpanBuilder:
    """
    Construit des spans candidats à partir des tokens d'un texte.

    Les spans sont continus dans le texte source et peuvent contenir
    plusieurs tokens consécutifs.
    """

    def __init__(self, max_tokens: int = 10) -> None:
        if max_tokens < 1:
            raise ValueError(
                "max_tokens doit être supérieur ou égal à 1."
            )

        self.max_tokens = max_tokens

    def build(
        self,
        text: str,
        tokens: list[TextToken],
    ) -> list[TextSpan]:
        if not isinstance(text, str):
            raise TypeError("Le texte doit être une chaîne.")

        if not tokens:
            return []

        spans: list[TextSpan] = []

        for start_index in range(len(tokens)):
            max_end = min(
                len(tokens),
                start_index + self.max_tokens,
            )

            for end_index in range(start_index, max_end):
                first = tokens[start_index]
                last = tokens[end_index]

                value = text[first.start:last.end]

                spans.append(
                    TextSpan(
                        value=value,
                        start=first.start,
                        end=last.end,
                        token_count=end_index - start_index + 1,
                    )
                )

        return spans