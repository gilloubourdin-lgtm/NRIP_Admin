from __future__ import annotations

import re

from app.models.text_token import TextToken


TOKEN_PATTERN = re.compile(
    r"""
    \d+(?:[.,]\d+)?\s?%
    |
    \d+(?:[.,]\d+)?(?:-[A-Za-zÀ-ÖØ-öø-ÿ0-9]+)*
    |
    [A-Za-zÀ-ÖØ-öø-ÿα-ωΑ-Ω]+
        (?:[-'][A-Za-zÀ-ÖØ-öø-ÿα-ωΑ-Ω0-9]+)*
    """,
    flags=re.VERBOSE | re.UNICODE,
)


class EntityTokenizer:
    """
    Tokenizer léger adapté aux textes scientifiques.

    Il conserve notamment :
    - les mots simples ;
    - les mots composés avec tiret ;
    - les apostrophes ;
    - les valeurs numériques ;
    - certains identifiants alphanumériques ;
    - les positions exactes dans le texte.
    """

    def tokenize(self, text: str) -> list[TextToken]:
        if not isinstance(text, str):
            raise TypeError("Le texte à tokeniser doit être une chaîne.")

        if not text:
            return []

        return [
            TextToken(
                value=match.group(0),
                start=match.start(),
                end=match.end(),
            )
            for match in TOKEN_PATTERN.finditer(text)
        ]