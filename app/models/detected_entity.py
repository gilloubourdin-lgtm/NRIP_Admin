from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class DetectedEntity:
    """
    Entité scientifique détectée dans un document.

    Une entité conserve :
    - la forme réellement trouvée dans le texte ;
    - sa forme canonique normalisée ;
    - sa catégorie scientifique ;
    - la preuve de son origine dans le document.
    """

    value: str
    canonical: str
    category: str

    confidence: float = 1.0

    source_line: int | None = None
    source_text: str | None = None
    source_section: str | None = None

    extractor: str = "rule_based"
    taxonomy_id: str | None = None

    def __post_init__(self) -> None:
        self.value = self.value.strip()
        self.canonical = self.canonical.strip()
        self.category = self.category.strip().lower()

        if not self.value:
            raise ValueError("DetectedEntity.value ne peut pas être vide.")

        if not self.canonical:
            raise ValueError("DetectedEntity.canonical ne peut pas être vide.")

        if not self.category:
            raise ValueError("DetectedEntity.category ne peut pas être vide.")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "DetectedEntity.confidence doit être compris entre 0 et 1."
            )

        if self.source_line is not None and self.source_line < 1:
            raise ValueError(
                "DetectedEntity.source_line doit être supérieur ou égal à 1."
            )

    @property
    def normalized_key(self) -> str:
        """
        Clé stable permettant de comparer et dédupliquer les entités.
        """
        return f"{self.category}:{self.canonical.casefold()}"

    def matches(self, value: str) -> bool:
        """
        Vérifie si une valeur correspond à la forme détectée
        ou à la forme canonique.
        """
        candidate = value.strip().casefold()

        return candidate in {
            self.value.casefold(),
            self.canonical.casefold(),
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)