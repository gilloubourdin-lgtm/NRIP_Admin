from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.models.detected_entity import DetectedEntity
from app.models.document_relation import DocumentRelation


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class ScientificDocument:
    """
    Représentation normalisée d'un document scientifique.

    Ce modèle devient le format interne commun de NRIP_Admin.
    Les moteurs de recherche, d'extraction, de graphe et
    d'assistance scientifique travailleront avec cet objet.
    """

    # Identification
    document_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    title: str = ""
    abstract: str | None = None
    language: str = "fr"
    document_type: str = "unknown"
    status: str = "active"
    version: str | None = None

    # Bibliographie
    authors: list[str] = field(default_factory=list)
    institutions: list[str] = field(default_factory=list)
    year: int | None = None
    journal: str | None = None
    doi: str | None = None
    projects: list[str] = field(default_factory=list)
    funding_sources: list[str] = field(default_factory=list)

    # Localisation
    filename: str = ""
    relative_path: str = ""
    source_format: str = "markdown"
    file_created_at: datetime | None = None
    file_modified_at: datetime | None = None

    # Contenu
    markdown: str = ""
    plain_text: str = ""
    sections: dict[str, str] = field(default_factory=dict)

    # Classification scientifique
    keywords: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)

    # Entités détectées
    entities: list[DetectedEntity] = field(default_factory=list)

    # Synthèse et conclusions
    summary: str | None = None
    conclusions: list[str] = field(default_factory=list)

    # Relations et graphe
    relations: list[DocumentRelation] = field(default_factory=list)
    cited_references: list[str] = field(default_factory=list)
    similar_document_ids: list[str] = field(default_factory=list)

    # Métadonnées d'indexation
    confidence_score: float = 0.0
    indexed_at: datetime = field(default_factory=_utc_now)
    extraction_engine: str = "nrip-rule-based-v0.2"
    schema_version: str = "0.2"

    def __post_init__(self) -> None:
        self.document_id = self.document_id.strip()
        self.title = self.title.strip()
        self.language = self.language.strip().lower() or "unknown"
        self.document_type = (
            self.document_type.strip().lower() or "unknown"
        )
        self.status = self.status.strip().lower() or "active"
        self.filename = self.filename.strip()
        self.relative_path = self.relative_path.strip()

        if not self.document_id:
            raise ValueError(
                "ScientificDocument.document_id ne peut pas être vide."
            )

        if self.year is not None and not 1500 <= self.year <= 2200:
            raise ValueError(
                "ScientificDocument.year est hors de la plage autorisée."
            )

        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError(
                "ScientificDocument.confidence_score doit être "
                "compris entre 0 et 1."
            )

        self.authors = self._deduplicate_strings(self.authors)
        self.institutions = self._deduplicate_strings(
            self.institutions
        )
        self.projects = self._deduplicate_strings(self.projects)
        self.funding_sources = self._deduplicate_strings(
            self.funding_sources
        )
        self.keywords = self._deduplicate_strings(self.keywords)
        self.topics = self._deduplicate_strings(self.topics)
        self.conclusions = self._deduplicate_strings(
            self.conclusions
        )
        self.cited_references = self._deduplicate_strings(
            self.cited_references
        )
        self.similar_document_ids = self._deduplicate_strings(
            self.similar_document_ids
        )

        self.entities = self._deduplicate_entities(self.entities)
        self.relations = self._deduplicate_relations(self.relations)

    @staticmethod
    def _deduplicate_strings(values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            cleaned = value.strip()

            if not cleaned:
                continue

            key = cleaned.casefold()

            if key in seen:
                continue

            seen.add(key)
            result.append(cleaned)

        return result

    @staticmethod
    def _deduplicate_entities(
        entities: list[DetectedEntity],
    ) -> list[DetectedEntity]:
        result: list[DetectedEntity] = []
        seen: set[str] = set()

        for entity in entities:
            key = entity.normalized_key

            if key in seen:
                continue

            seen.add(key)
            result.append(entity)

        return result

    @staticmethod
    def _deduplicate_relations(
        relations: list[DocumentRelation],
    ) -> list[DocumentRelation]:
        result: list[DocumentRelation] = []
        seen: set[str] = set()

        for relation in relations:
            key = relation.relation_key

            if key in seen:
                continue

            seen.add(key)
            result.append(relation)

        return result

    @property
    def path(self) -> Path | None:
        if not self.relative_path:
            return None

        return Path(self.relative_path)

    @property
    def display_title(self) -> str:
        if self.title:
            return self.title

        if self.filename:
            return Path(self.filename).stem

        return "Document sans titre"

    @property
    def entity_count(self) -> int:
        return len(self.entities)

    @property
    def relation_count(self) -> int:
        return len(self.relations)

    @property
    def word_count(self) -> int:
        source = self.plain_text or self.markdown
        return len(source.split())

    @property
    def is_indexed(self) -> bool:
        return bool(
            self.entities
            or self.keywords
            or self.topics
            or self.summary
        )

    def add_entity(self, entity: DetectedEntity) -> bool:
        """
        Ajoute une entité si elle n'existe pas déjà.

        Retourne True si l'entité a été ajoutée.
        """
        existing_keys = {
            current.normalized_key
            for current in self.entities
        }

        if entity.normalized_key in existing_keys:
            return False

        self.entities.append(entity)
        return True

    def add_relation(self, relation: DocumentRelation) -> bool:
        """
        Ajoute une relation si elle n'existe pas déjà.
        """
        existing_keys = {
            current.relation_key
            for current in self.relations
        }

        if relation.relation_key in existing_keys:
            return False

        self.relations.append(relation)
        return True

    def entities_by_category(
        self,
        category: str,
    ) -> list[DetectedEntity]:
        normalized_category = category.strip().lower()

        return [
            entity
            for entity in self.entities
            if entity.category == normalized_category
        ]

    def canonical_entities(
        self,
        category: str | None = None,
    ) -> list[str]:
        selected = (
            self.entities_by_category(category)
            if category
            else self.entities
        )

        return self._deduplicate_strings(
            [entity.canonical for entity in selected]
        )

    def entity_statistics(self) -> dict[str, int]:
        statistics: dict[str, int] = {}

        for entity in self.entities:
            statistics[entity.category] = (
                statistics.get(entity.category, 0) + 1
            )

        return dict(sorted(statistics.items()))

    def calculate_confidence(self) -> float:
        """
        Calcule un premier score simple de qualité d'indexation.

        Ce calcul sera remplacé plus tard par le Knowledge Health Engine.
        """
        components: list[float] = []

        if self.title:
            components.append(1.0)

        if self.authors:
            components.append(1.0)

        if self.year is not None:
            components.append(1.0)

        if self.plain_text or self.markdown:
            components.append(1.0)

        if self.entities:
            entity_confidence = sum(
                entity.confidence for entity in self.entities
            ) / len(self.entities)
            components.append(entity_confidence)

        if self.keywords or self.topics:
            components.append(0.8)

        if not components:
            self.confidence_score = 0.0
            return self.confidence_score

        self.confidence_score = round(
            sum(components) / len(components),
            4,
        )

        return self.confidence_score

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)