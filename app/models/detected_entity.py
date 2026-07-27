from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class DetectedEntity:
    """
    Entité scientifique détectée dans un document.

    Une entité conserve :
    - la forme réellement trouvée dans le texte ;
    - sa forme canonique normalisée ;
    - sa catégorie scientifique ;
    - sa position dans le texte ;
    - la preuve de son origine dans le document ;
    - la méthode ayant permis sa détection.
    """

    value: str
    canonical: str
    category: str

    confidence: float = 1.0

    taxonomy_id: str | None = None

    start: int | None = None
    end: int | None = None

    source_line: int | None = None
    source_text: str | None = None
    source_section: str | None = None

    extractor: str = "rule_based"
    match_type: str = "exact"

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.value = self.value.strip()
        self.canonical = self.canonical.strip()
        self.category = self.category.strip().lower()
        self.extractor = self.extractor.strip().lower()
        self.match_type = self.match_type.strip().lower()

        if self.taxonomy_id is not None:
            self.taxonomy_id = self.taxonomy_id.strip() or None

        if not self.value:
            raise ValueError(
                "DetectedEntity.value ne peut pas être vide."
            )

        if not self.canonical:
            raise ValueError(
                "DetectedEntity.canonical ne peut pas être vide."
            )

        if not self.category:
            raise ValueError(
                "DetectedEntity.category ne peut pas être vide."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "DetectedEntity.confidence doit être compris entre 0 et 1."
            )

        if self.source_line is not None and self.source_line < 1:
            raise ValueError(
                "DetectedEntity.source_line doit être supérieur ou égal à 1."
            )

        if self.start is not None and self.start < 0:
            raise ValueError(
                "DetectedEntity.start doit être supérieur ou égal à 0."
            )

        if self.end is not None and self.end < 0:
            raise ValueError(
                "DetectedEntity.end doit être supérieur ou égal à 0."
            )

        if (
            self.start is not None
            and self.end is not None
            and self.end <= self.start
        ):
            raise ValueError(
                "DetectedEntity.end doit être strictement supérieur à start."
            )

        if (self.start is None) != (self.end is None):
            raise ValueError(
                "DetectedEntity.start et end doivent être fournis ensemble."
            )

    @property
    def normalized_key(self) -> str:
        """
        Clé stable permettant de comparer et dédupliquer les entités.
        """
        if self.taxonomy_id:
            return self.taxonomy_id.casefold()

        return f"{self.category}:{self.canonical.casefold()}"

    @property
    def length(self) -> int | None:
        """
        Longueur de l'entité dans le texte source.
        """
        if self.start is None or self.end is None:
            return None

        return self.end - self.start

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

    def overlaps(self, other: DetectedEntity) -> bool:
        """
        Vérifie si deux entités occupent une zone commune du texte.
        """
        if (
            self.start is None
            or self.end is None
            or other.start is None
            or other.end is None
        ):
            return False

        return self.start < other.end and other.start < self.end

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)