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

    MAX_CONTAINMENT_CONFIDENCE_GAP = 0.10

    @staticmethod
    def _contains(
        outer: DetectedEntity,
        inner: DetectedEntity,
    ) -> bool:
        if (
            outer.start is None
            or outer.end is None
            or inner.start is None
            or inner.end is None
        ):
            return False

        return (
            outer.start <= inner.start
            and outer.end >= inner.end
            and (
                outer.start < inner.start
                or outer.end > inner.end
            )
        )


    def _prefer_containing_candidate(
        self,
        candidate: DetectedEntity,
        existing: DetectedEntity,
    ) -> bool:
        if not self._contains(candidate, existing):
            return False

        return (
            candidate.confidence
            >= existing.confidence
            - self.MAX_CONTAINMENT_CONFIDENCE_GAP
        )

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
        Résout les détections concurrentes qui se chevauchent.

        Une expression reconnue qui englobe complètement une expression
        plus courte peut être préférée lorsque leurs confiances restent
        suffisamment proches.
        """
        ranked = self.rank(entities)

        selected: list[DetectedEntity] = []

        for candidate in ranked:
            overlapping = [
                existing
                for existing in selected
                if candidate.overlaps(existing)
            ]

            if not overlapping:
                selected.append(candidate)
                continue

            if all(
                self._prefer_containing_candidate(
                    candidate,
                    existing,
                )
                for existing in overlapping
            ):
                selected = [
                    existing
                    for existing in selected
                    if existing not in overlapping
                ]
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