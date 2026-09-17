from __future__ import annotations

from app.models.scientific_document import ScientificDocument
from app.services.entity_extraction.extractor import EntityExtractor


class KnowledgeEngine:
    """
    Orchestre l'enrichissement déterministe d'un document scientifique.

    V1 :
        ScientificDocument
        -> extraction des entités depuis plain_text
        -> ajout des occurrences détectées
        -> recalcul du score de confiance
        -> ScientificDocument enrichi
    """

    def __init__(
        self,
        *,
        entity_extractor: EntityExtractor | None = None,
    ) -> None:
        self.entity_extractor = (
            entity_extractor
            if entity_extractor is not None
            else EntityExtractor()
        )

    def enrich(
        self,
        document: ScientificDocument,
    ) -> ScientificDocument:
        """
        Enrichit un ScientificDocument avec les entités détectées.

        Le document fourni est modifié en place puis retourné.
        """
        if not isinstance(document, ScientificDocument):
            raise TypeError(
                "document doit être un ScientificDocument."
            )

        entities = self.entity_extractor.extract(
            document.plain_text
        )

        for entity in entities:
            document.add_entity(entity)

        document.calculate_confidence()

        return document
