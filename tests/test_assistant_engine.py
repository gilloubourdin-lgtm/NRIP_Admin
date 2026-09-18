from app.models.knowledge_graph import (
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
)
from app.services.assistant_engine import (
    AssistantEngine,
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
