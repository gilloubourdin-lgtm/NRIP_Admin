from __future__ import annotations

from app.models.detected_entity import DetectedEntity
from app.services.entity_extraction.matcher import EntityMatcher
from app.services.entity_extraction.scorer import EntityScorer
from app.services.entity_extraction.spans import SpanBuilder
from app.services.entity_extraction.tokenizer import EntityTokenizer
from app.services.ontology import OntologyEngine
from app.services.taxonomy import TaxonomyEngine


class EntityExtractor:
    """
    Orchestre l'extraction déterministe des entités scientifiques.

    Pipeline :
        texte
        -> tokenisation
        -> génération de spans candidats
        -> résolution taxonomique
        -> résolution des chevauchements
        -> entités finales ordonnées
    """

    def __init__(
        self,
        *,
        taxonomy: TaxonomyEngine | None = None,
        ontology: OntologyEngine | None = None,
        tokenizer: EntityTokenizer | None = None,
        span_builder: SpanBuilder | None = None,
        scorer: EntityScorer | None = None,
    ) -> None:
        self.taxonomy = taxonomy or TaxonomyEngine()
        self.ontology = ontology or OntologyEngine()

        self.tokenizer = tokenizer or EntityTokenizer()
        self.span_builder = span_builder or SpanBuilder()

        self.matcher = EntityMatcher(
            taxonomy=self.taxonomy,
            ontology=self.ontology,
        )

        self.scorer = scorer or EntityScorer()

    def extract(
        self,
        text: str,
        *,
        source_line: int | None = None,
        source_section: str | None = None,
    ) -> list[DetectedEntity]:
        """
        Extrait les entités scientifiques connues depuis un texte.
        """
        if not isinstance(text, str):
            raise TypeError(
                "Le texte à analyser doit être une chaîne."
            )

        if not text.strip():
            return []

        tokens = self.tokenizer.tokenize(text)

        if not tokens:
            return []

        spans = self.span_builder.build(text, tokens)

        candidates: list[DetectedEntity] = []

        for span in spans:
            entity = self.matcher.match(
                span.value,
                start=span.start,
                end=span.end,
                source_line=source_line,
                source_text=text,
                source_section=source_section,
            )

            if entity is not None:
                candidates.append(entity)

        return self.scorer.resolve_overlaps(candidates)