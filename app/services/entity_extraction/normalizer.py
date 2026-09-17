from __future__ import annotations

import re
import unicodedata


class EntityNormalizer:
    """
    Normalise une forme textuelle pour permettre sa comparaison.

    La normalisation est volontairement non sémantique :
    elle harmonise la typographie mais ne décide pas que deux
    termes scientifiques différents représentent le même concept.
    """

    _DASHES = str.maketrans({
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
    })

    _APOSTROPHES = str.maketrans({
        "\u2018": "'",
        "\u2019": "'",
        "\u02bc": "'",
    })

    _SEPARATORS = re.compile(r"[\s\-_/]+")
    _MULTIPLE_SPACES = re.compile(r"\s+")

    def normalize(self, value: str) -> str:
        """
        Retourne une clé normalisée adaptée à la comparaison.

        Exemples :
            "GC-MS"            -> "gcms"
            "GC/MS"            -> "gcms"
            "GC MS"            -> "gcms"
            "4-ethylphenol"    -> "4ethylphenol"
            "4 ethylphenol"    -> "4ethylphenol"
        """
        if not isinstance(value, str):
            raise TypeError(
                "La valeur à normaliser doit être une chaîne."
            )

        value = value.strip()

        if not value:
            return ""

        value = value.translate(self._DASHES)
        value = value.translate(self._APOSTROPHES)

        value = unicodedata.normalize("NFKC", value)
        value = value.casefold()

        value = self._SEPARATORS.sub("", value)

        return value

    def normalize_phrase(self, value: str) -> str:
        """
        Normalise une phrase tout en conservant les séparations
        entre les mots.

        Utile pour les noms scientifiques composés.
        """
        if not isinstance(value, str):
            raise TypeError(
                "La valeur à normaliser doit être une chaîne."
            )

        value = value.strip()

        if not value:
            return ""

        value = value.translate(self._DASHES)
        value = value.translate(self._APOSTROPHES)

        value = unicodedata.normalize("NFKC", value)
        value = value.casefold()

        value = self._MULTIPLE_SPACES.sub(" ", value)

        return value