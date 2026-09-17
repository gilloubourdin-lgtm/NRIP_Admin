from __future__ import annotations

from app.models.detected_entity import DetectedEntity
from app.models.taxonomy_node import TaxonomyNode
from app.services.entity_extraction.normalizer import EntityNormalizer
from app.services.ontology import OntologyEngine
from app.services.taxonomy import TaxonomyEngine


class EntityMatcher:
    """
    Résout une forme textuelle vers une entité scientifique canonique.

    Stratégie V1 :
    1. correspondance directe dans la taxonomie ;
    2. correspondance après normalisation typographique ;
    3. résolution explicite d'un alias par l'ontologie ;
    4. recherche du terme canonique obtenu dans la taxonomie.

    Aucun fuzzy matching n'est effectué.
    """

    def __init__(
        self,
        taxonomy: TaxonomyEngine,
        ontology: OntologyEngine,
        normalizer: EntityNormalizer | None = None,
    ) -> None:
        self.taxonomy = taxonomy
        self.ontology = ontology
        self.normalizer = normalizer or EntityNormalizer()

    def match(
        self,
        value: str,
        *,
        start: int | None = None,
        end: int | None = None,
        source_line: int | None = None,
        source_text: str | None = None,
        source_section: str | None = None,
    ) -> DetectedEntity | None:
        if not isinstance(value, str):
            raise TypeError(
                "La valeur à rechercher doit être une chaîne."
            )

        cleaned = value.strip()

        if not cleaned:
            return None

        # 1. Recherche directe dans la taxonomie.
        node = self.taxonomy.find(cleaned)

        if node is not None:
            if cleaned.casefold() == node.name.casefold():
                match_type = "exact"
                confidence = 1.0
            else:
                match_type = "alias"
                confidence = 0.95

            return self._build_entity(
                value=cleaned,
                node=node,
                confidence=confidence,
                match_type=match_type,
                start=start,
                end=end,
                source_line=source_line,
                source_text=source_text,
                source_section=source_section,
            )

        # 2. Recherche après normalisation typographique.
        normalized = self.normalizer.normalize(cleaned)

        if normalized:
            node = self.taxonomy.find(normalized)

            if node is not None:
                return self._build_entity(
                    value=cleaned,
                    node=node,
                    confidence=0.95,
                    match_type="normalized",
                    start=start,
                    end=end,
                    source_line=source_line,
                    source_text=source_text,
                    source_section=source_section,
                )

        # 3. Alias explicitement connu de l'ontologie.
        canonical = self.ontology.find_alias(cleaned)

        if canonical is not None:
            node = self.taxonomy.find(canonical)

            if node is not None:
                return self._build_entity(
                    value=cleaned,
                    node=node,
                    confidence=0.90,
                    match_type="ontology",
                    start=start,
                    end=end,
                    source_line=source_line,
                    source_text=source_text,
                    source_section=source_section,
                )

        return None

    @staticmethod
    def _build_entity(
        *,
        value: str,
        node: TaxonomyNode,
        confidence: float,
        match_type: str,
        start: int | None,
        end: int | None,
        source_line: int | None,
        source_text: str | None,
        source_section: str | None,
    ) -> DetectedEntity:
        return DetectedEntity(
            value=value,
            canonical=node.name,
            category=node.category,
            confidence=confidence,
            taxonomy_id=node.id,
            start=start,
            end=end,
            source_line=source_line,
            source_text=source_text,
            source_section=source_section,
            extractor="entity_matcher",
            match_type=match_type,
        )