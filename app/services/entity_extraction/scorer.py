from __future__ import annotations

from app.models.detected_entity import DetectedEntity


class EntityScorer:
    """
    Classe et sélectionne les entités détectées.

    Les critères sont déterministes :
    1. niveau de confiance ;
    2. qualité du type de correspondance ;
    3. longueur du span ;
    4. position dans le texte.

    Lors de chevauchements, le meilleur candidat est conservé.
    """

    MATCH_TYPE_PRIORITY = {
        "exact": 4,
        "alias": 3,
        "normalized": 2,
        "ontology": 1,
    }

    def score(self, entity: DetectedEntity) -> tuple[float, int, int]:
        """
        Retourne une clé de classement pour une entité.

        Une valeur plus grande représente un candidat préférable.
        """
        match_priority = self.MATCH_TYPE_PRIORITY.get(
            entity.match_type,
            0,
        )

        length = entity.length or len(entity.value)

        return (
            entity.confidence,
            match_priority,
            length,
        )

    def rank(
        self,
        entities: list[DetectedEntity],
    ) -> list[DetectedEntity]:
        """
        Classe les candidats du meilleur au moins prioritaire.
        """
        return sorted(
            entities,
            key=lambda entity: (
                -self.score(entity)[0],
                -self.score(entity)[1],
                -self.score(entity)[2],
                entity.start
                if entity.start is not None
                else float("inf"),
                entity.canonical.casefold(),
            ),
        )

    def resolve_overlaps(
        self,
        entities: list[DetectedEntity],
    ) -> list[DetectedEntity]:
        """
        Supprime les détections concurrentes qui se chevauchent.

        Les meilleurs candidats sont sélectionnés en premier.
        Le résultat final est réordonné selon sa position dans le texte.
        """
        ranked = self.rank(entities)

        selected: list[DetectedEntity] = []

        for candidate in ranked:
            if any(
                candidate.overlaps(existing)
                for existing in selected
            ):
                continue

            selected.append(candidate)

        return sorted(
            selected,
            key=lambda entity: (
                entity.start
                if entity.start is not None
                else float("inf"),
                entity.end
                if entity.end is not None
                else float("inf"),
                entity.canonical.casefold(),
            ),
        )