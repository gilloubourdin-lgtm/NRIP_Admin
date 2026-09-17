from app.services.document_parser import DocumentParser
from app.services.knowledge_engine import KnowledgeEngine


def test_parser_to_knowledge_engine_pipeline():
    markdown = """---
document_id: NRIP-TEST
title: Pipeline scientifique
authors:
  - NRIP
year: 2026
---

# Pipeline scientifique

## Contexte

Le vin est étudié dans un référentiel réglementaire.
"""

    parser = DocumentParser()
    engine = KnowledgeEngine()

    document = parser.parse_text(
        markdown,
        filename="NRIP-TEST.md",
        relative_path="tests/NRIP-TEST.md",
    )

    result = engine.enrich(document)

    assert result is document
    assert document.document_id == "NRIP-TEST"
    assert document.title == "Pipeline scientifique"
    assert document.plain_text

    canonical = set(
        document.canonical_entities()
    )

    assert "Vin" in canonical
    assert "Référentiel réglementaire" in canonical

    assert document.entity_count >= 2
    assert document.confidence_score > 0.0
