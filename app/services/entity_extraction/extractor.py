from app.models.detected_entity import DetectedEntity


class EntityExtractor:

    def extract(self, text: str) -> list[DetectedEntity]:
        raise NotImplementedError