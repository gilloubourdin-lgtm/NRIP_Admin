from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


ALLOWED_RELATION_TYPES = {
    "references",
    "cites",
    "mentions",
    "similar_to",
    "continues",
    "updates",
    "replaces",
    "supports",
    "contradicts",
    "belongs_to_project",
    "authored_by",
    "uses_method",
    "studies",
    "produced_by",
}


@dataclass(slots=True)
class DocumentRelation:
    """
    Relation entre un document et un autre document, une entité,
    un projet, une personne ou un concept scientifique.
    """

    source_id: str
    target_id: str
    relation_type: str

    confidence: float = 1.0

    source_line: int | None = None
    source_text: str | None = None

    created_by: str = "system"
    bidirectional: bool = False

    def __post_init__(self) -> None:
        self.source_id = self.source_id.strip()
        self.target_id = self.target_id.strip()
        self.relation_type = self.relation_type.strip().lower()

        if not self.source_id:
            raise ValueError("DocumentRelation.source_id ne peut pas être vide.")

        if not self.target_id:
            raise ValueError("DocumentRelation.target_id ne peut pas être vide.")

        if self.source_id == self.target_id:
            raise ValueError(
                "Une relation ne peut pas relier un élément à lui-même."
            )

        if not self.relation_type:
            raise ValueError(
                "DocumentRelation.relation_type ne peut pas être vide."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "DocumentRelation.confidence doit être compris entre 0 et 1."
            )

        if self.source_line is not None and self.source_line < 1:
            raise ValueError(
                "DocumentRelation.source_line doit être supérieur ou égal à 1."
            )

    @property
    def relation_key(self) -> str:
        return (
            f"{self.source_id}:"
            f"{self.relation_type}:"
            f"{self.target_id}"
        )

    @property
    def is_known_relation_type(self) -> bool:
        return self.relation_type in ALLOWED_RELATION_TYPES

    def reverse(self) -> "DocumentRelation":
        """
        Crée la relation inverse.

        Cette méthode est surtout utile pour les relations
        bidirectionnelles ou pour la construction du graphe.
        """
        return DocumentRelation(
            source_id=self.target_id,
            target_id=self.source_id,
            relation_type=self.relation_type,
            confidence=self.confidence,
            source_line=self.source_line,
            source_text=self.source_text,
            created_by=self.created_by,
            bidirectional=self.bidirectional,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)