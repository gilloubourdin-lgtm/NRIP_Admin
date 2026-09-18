from app.models.knowledge_graph import (
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
)
from app.services.assistant_engine import (
    AssistantEngine,
    AssistantEvidence,
    AssistantResult,
)


def make_graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()

    nodes = [
        GraphNode(
            node_id="document:NRIP-001",
            node_type="document",
            label="Brettanomyces study",
        ),
        GraphNode(
            node_id=(
                "concept:"
                "organism.microorganism.yeast.brettanomyces"
            ),
            node_type="concept",
            label="Brettanomyces",
        ),
        GraphNode(
            node_id=(
                "concept:"
                "organism.microorganism.yeast"
            ),
            node_type="concept",
            label="Levure",
        ),
        GraphNode(
            node_id="concept:organism.microorganism",
            node_type="concept",
            label="Microorganisme",
        ),
        GraphNode(
            node_id="concept:organism",
            node_type="concept",
            label="Organisme vivant",
        ),
    ]

    for node in nodes:
        graph.add_node(node)

    edges = [
        GraphEdge(
            source_id="document:NRIP-001",
            target_id=(
                "concept:"
                "organism.microorganism.yeast.brettanomyces"
            ),
            relation_type="mentions",
        ),
        GraphEdge(
            source_id=(
                "concept:"
                "organism.microorganism.yeast.brettanomyces"
            ),
            target_id=(
                "concept:"
                "organism.microorganism.yeast"
            ),
            relation_type="is_a",
        ),
        GraphEdge(
            source_id=(
                "concept:"
                "organism.microorganism.yeast"
            ),
            target_id="concept:organism.microorganism",
            relation_type="is_a",
        ),
        GraphEdge(
            source_id="concept:organism.microorganism",
            target_id="concept:organism",
            relation_type="is_a",
        ),
    ]

    for edge in edges:
        graph.add_edge(edge)

    return graph


def test_assistant_resolves_canonical_concept():
    engine = AssistantEngine(graph=make_graph())

    result = engine.lookup("Brettanomyces")

    assert isinstance(result, AssistantResult)
    assert result.found is True
    assert result.query == "Brettanomyces"
    assert result.concept_id == (
        "concept:"
        "organism.microorganism.yeast.brettanomyces"
    )
    assert result.concept_label == "Brettanomyces"


def test_assistant_resolves_taxonomy_alias():
    engine = AssistantEngine(graph=make_graph())

    result = engine.lookup("Dekkera")

    assert result.found is True
    assert result.concept_label == "Brettanomyces"
    assert result.concept_id == (
        "concept:"
        "organism.microorganism.yeast.brettanomyces"
    )


def test_assistant_returns_ancestors():
    engine = AssistantEngine(graph=make_graph())

    result = engine.lookup("Brettanomyces")

    assert [
        node.label
        for node in result.ancestors
    ] == [
        "Levure",
        "Microorganisme",
        "Organisme vivant",
    ]


def test_assistant_returns_documents():
    engine = AssistantEngine(graph=make_graph())

    result = engine.lookup("Brettanomyces")

    assert [
        node.node_id
        for node in result.documents
    ] == [
        "document:NRIP-001",
    ]


def test_assistant_returns_not_found_result():
    engine = AssistantEngine(graph=make_graph())

    result = engine.lookup(
        "concept scientifique inexistant"
    )

    assert result.found is False
    assert result.concept_id is None
    assert result.concept_label is None
    assert result.ancestors == []
    assert result.documents == []


def test_assistant_rejects_empty_query():
    import pytest

    engine = AssistantEngine(graph=make_graph())

    with pytest.raises(ValueError):
        engine.lookup("   ")


def test_assistant_rejects_non_string_query():
    import pytest

    engine = AssistantEngine(graph=make_graph())

    with pytest.raises(TypeError):
        engine.lookup(None)


def test_assistant_handles_taxonomy_concept_absent_from_graph():
    engine = AssistantEngine(graph=make_graph())

    result = engine.lookup("GC-MS")

    assert result.found is False
    assert result.concept_id == (
        "concept:analysis.chromatography.gc_ms"
    )
    assert result.concept_label == "GC-MS"
    assert result.ancestors == []
    assert result.documents == []


def test_assistant_real_scientific_pipeline():
    from app.models.scientific_document import (
        ScientificDocument,
    )
    from app.services.graph_builder import GraphBuilder
    from app.services.knowledge_engine import KnowledgeEngine

    document = ScientificDocument(
        document_id="NRIP-ASSISTANT-CHECK",
        title="Brettanomyces analysis",
        plain_text=(
            "Dekkera est analysee par GC-MS."
        ),
    )

    KnowledgeEngine().enrich(document)

    graph = GraphBuilder().build([document])
    engine = AssistantEngine(graph=graph)

    result = engine.lookup("Dekkera")

    assert result.found is True
    assert result.concept_label == "Brettanomyces"

    assert [
        node.label
        for node in result.ancestors
    ] == [
        "Levure",
        "Microorganisme",
        "Organisme vivant",
    ]

    assert [
        node.node_id
        for node in result.documents
    ] == [
        "document:NRIP-ASSISTANT-CHECK",
    ]


def test_assistant_returns_evidence():
    from app.models.detected_entity import DetectedEntity

    graph = make_graph()

    edge = graph.edges[
        (
            "document:NRIP-001:"
            "mentions:"
            "concept:"
            "organism.microorganism.yeast.brettanomyces"
        )
    ]

    edge.add_occurrence(
        DetectedEntity(
            value="Dekkera",
            canonical="Brettanomyces",
            category="microorganism",
            taxonomy_id=(
                "organism.microorganism."
                "yeast.brettanomyces"
            ),
            start=12,
            end=19,
            source_line=3,
            source_text=(
                "Presence de Dekkera dans le vin."
            ),
            source_section="Resultats",
            confidence=0.95,
            match_type="alias",
        )
    )

    engine = AssistantEngine(graph=graph)

    result = engine.lookup("Dekkera")

    assert len(result.evidence) == 1

    evidence = result.evidence[0]

    assert isinstance(
        evidence,
        AssistantEvidence,
    )
    assert evidence.document.node_id == (
        "document:NRIP-001"
    )
    assert evidence.concept.label == (
        "Brettanomyces"
    )
    assert evidence.occurrence.value == "Dekkera"
    assert evidence.occurrence.start == 12
    assert evidence.occurrence.end == 19
    assert evidence.occurrence.source_line == 3
    assert evidence.occurrence.source_section == (
        "Resultats"
    )
    assert evidence.occurrence.confidence == 0.95
    assert evidence.occurrence.match_type == "alias"


def test_assistant_preserves_multiple_occurrences():
    from app.models.detected_entity import DetectedEntity

    graph = make_graph()

    edge = graph.edges[
        (
            "document:NRIP-001:"
            "mentions:"
            "concept:"
            "organism.microorganism.yeast.brettanomyces"
        )
    ]

    for start, end in [
        (10, 17),
        (50, 57),
    ]:
        edge.add_occurrence(
            DetectedEntity(
                value="Dekkera",
                canonical="Brettanomyces",
                category="microorganism",
                taxonomy_id=(
                    "organism.microorganism."
                    "yeast.brettanomyces"
                ),
                start=start,
                end=end,
            )
        )

    result = AssistantEngine(
        graph=graph
    ).lookup("Brettanomyces")

    assert len(result.evidence) == 2

    assert [
        evidence.occurrence.start
        for evidence in result.evidence
    ] == [
        10,
        50,
    ]


def test_assistant_not_found_has_no_evidence():
    result = AssistantEngine(
        graph=make_graph()
    ).lookup(
        "concept scientifique inexistant"
    )

    assert result.evidence == []


def test_assistant_real_pipeline_preserves_evidence():
    from app.models.scientific_document import (
        ScientificDocument,
    )
    from app.services.graph_builder import GraphBuilder
    from app.services.knowledge_engine import KnowledgeEngine

    text = (
        "Le vin contient Dekkera et peut etre "
        "analyse par GC-MS."
    )

    document = ScientificDocument(
        document_id="NRIP-EVIDENCE-CHECK",
        title="Evidence check",
        plain_text=text,
    )

    KnowledgeEngine().enrich(document)

    graph = GraphBuilder().build([document])

    result = AssistantEngine(
        graph=graph
    ).lookup("Dekkera")

    assert result.found is True
    assert result.concept_label == "Brettanomyces"
    assert len(result.evidence) == 1

    evidence = result.evidence[0]
    occurrence = evidence.occurrence

    assert evidence.document.node_id == (
        "document:NRIP-EVIDENCE-CHECK"
    )
    assert evidence.concept.label == "Brettanomyces"

    assert occurrence.value == "Dekkera"
    assert occurrence.canonical == "Brettanomyces"
    assert occurrence.taxonomy_id == (
        "organism.microorganism."
        "yeast.brettanomyces"
    )

    expected_start = text.index("Dekkera")

    assert occurrence.start == expected_start
    assert occurrence.end == (
        expected_start + len("Dekkera")
    )

    assert text[
        occurrence.start:occurrence.end
    ] == "Dekkera"
