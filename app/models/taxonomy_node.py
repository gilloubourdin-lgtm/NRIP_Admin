from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TaxonomyNode:
    """
    Représente un concept scientifique dans une taxonomie hiérarchique.

    L'identifiant est stable et destiné à être réutilisé dans :
    - les entités détectées ;
    - les relations scientifiques ;
    - le futur Knowledge Graph ;
    - l'assistant scientifique.
    """

    id: str
    name: str
    category: str
    parent_id: str | None = None
    description: str = ""
    aliases: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str | None = None

    def __post_init__(self) -> None:
        self.id = self.id.strip()
        self.name = self.name.strip()
        self.category = self.category.strip()
        self.parent_id = (
            self.parent_id.strip()
            if isinstance(self.parent_id, str) and self.parent_id.strip()
            else None
        )
        self.description = self.description.strip()

        self.aliases = self._clean_string_list(self.aliases)
        self.tags = self._clean_string_list(self.tags)

        if not self.id:
            raise ValueError("TaxonomyNode.id ne peut pas être vide.")

        if not self.name:
            raise ValueError("TaxonomyNode.name ne peut pas être vide.")

        if not self.category:
            raise ValueError(
                "TaxonomyNode.category ne peut pas être vide."
            )

        if self.parent_id == self.id:
            raise ValueError(
                "Un nœud taxonomique ne peut pas être son propre parent."
            )

        if not isinstance(self.metadata, dict):
            raise TypeError(
                "TaxonomyNode.metadata doit être un dictionnaire."
            )

    @staticmethod
    def _clean_string_list(values: list[str]) -> list[str]:
        if not isinstance(values, list):
            raise TypeError("La valeur doit être une liste.")

        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            if not isinstance(value, str):
                raise TypeError(
                    "Les alias et tags doivent être des chaînes."
                )

            cleaned = value.strip()

            if not cleaned:
                continue

            key = cleaned.casefold()

            if key in seen:
                continue

            seen.add(key)
            result.append(cleaned)

        return result

    @property
    def normalized_id(self) -> str:
        return self.id.casefold()

    @property
    def searchable_values(self) -> list[str]:
        return [self.name, *self.aliases]

    def matches(self, value: str) -> bool:
        searched = value.strip().casefold()

        if not searched:
            return False

        return any(
            candidate.casefold() == searched
            for candidate in self.searchable_values
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "parent_id": self.parent_id,
            "description": self.description,
            "aliases": list(self.aliases),
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "source": self.source,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        source: str | None = None,
    ) -> TaxonomyNode:
        if not isinstance(data, dict):
            raise TypeError(
                "Un nœud taxonomique doit être un dictionnaire."
            )

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            category=data.get("category", ""),
            parent_id=data.get("parent_id"),
            description=data.get("description", ""),
            aliases=data.get("aliases", []),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            source=source or data.get("source"),
        )