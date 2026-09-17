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


def test_multi_document_pipeline_shares_concept_node():
    from app.services.graph_builder import GraphBuilder

    first_markdown = """---
document_id: NRIP-TEST-001
title: Premier document
authors:
  - NRIP
year: 2026
---

# Premier document

Brettanomyces est étudié dans ce document.
"""

    second_markdown = """---
document_id: NRIP-TEST-002
title: Deuxième document
authors:
  - NRIP
year: 2026
---

# Deuxième document

Une seconde étude concerne Brettanomyces.
"""

    parser = DocumentParser()
    engine = KnowledgeEngine()
    builder = GraphBuilder()

    first = parser.parse_text(
        first_markdown,
        filename="NRIP-TEST-001.md",
        relative_path="tests/NRIP-TEST-001.md",
    )

    second = parser.parse_text(
        second_markdown,
        filename="NRIP-TEST-002.md",
        relative_path="tests/NRIP-TEST-002.md",
    )

    engine.enrich(first)
    engine.enrich(second)

    graph = builder.build([first, second])

    concept_id = (
        "concept:"
        "organism.microorganism.yeast.brettanomyces"
    )

    assert "document:NRIP-TEST-001" in graph.nodes
    assert "document:NRIP-TEST-002" in graph.nodes
    assert concept_id in graph.nodes

    matching_concept_nodes = [
        node
        for node in graph.nodes.values()
        if node.node_id == concept_id
    ]

    mention_edges = [
        edge
        for edge in graph.edges.values()
        if (
            edge.relation_type == "mentions"
            and edge.target_id == concept_id
        )
    ]

    assert len(matching_concept_nodes) == 1
    assert len(mention_edges) == 2

    assert {
        edge.source_id
        for edge in mention_edges
    } == {
        "document:NRIP-TEST-001",
        "document:NRIP-TEST-002",
    }

    assert all(
        len(edge.occurrences) == 1
        for edge in mention_edges
    )
