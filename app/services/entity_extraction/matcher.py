from app.models.detected_entity import DetectedEntity


class Matcher:
    """
    Recherche les entités dans la taxonomie.
    """

    def match(self, text: str) -> list[DetectedEntity]:
        raise NotImplementedError