from app.models.knowledge_graph import (
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
)
from app.services.graph_query_service import GraphQueryService


def make_graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()

    nodes = [
        GraphNode(
            node_id="document:NRIP-001",
            node_type="document",
            label="Document 1",
        ),
        GraphNode(
            node_id="document:NRIP-002",
            node_type="document",
            label="Document 2",
        ),
        GraphNode(
            node_id="concept:brettanomyces",
            node_type="concept",
            label="Brettanomyces",
        ),
        GraphNode(
            node_id="concept:yeast",
            node_type="concept",
            label="Levure",
        ),
        GraphNode(
            node_id="concept:microorganism",
            node_type="concept",
            label="Microorganisme",
        ),
    ]

    for node in nodes:
        graph.add_node(node)

    edges = [
        GraphEdge(
            source_id="document:NRIP-001",
            target_id="concept:brettanomyces",
            relation_type="mentions",
        ),
        GraphEdge(
            source_id="document:NRIP-002",
            target_id="concept:brettanomyces",
            relation_type="mentions",
        ),
        GraphEdge(
            source_id="concept:brettanomyces",
            target_id="concept:yeast",
            relation_type="is_a",
        ),
        GraphEdge(
            source_id="concept:yeast",
            target_id="concept:microorganism",
            relation_type="is_a",
        ),
    ]

    for edge in edges:
        graph.add_edge(edge)

    return graph


def test_concepts_for_document():
    service = GraphQueryService(make_graph())

    nodes = service.concepts_for_document("NRIP-001")

    assert [node.label for node in nodes] == [
        "Brettanomyces",
    ]


def test_documents_for_concept():
    service = GraphQueryService(make_graph())

    nodes = service.documents_for_concept(
        "concept:brettanomyces"
    )

    assert {
        node.node_id
        for node in nodes
    } == {
        "document:NRIP-001",
        "document:NRIP-002",
    }


def test_parents_of():
    service = GraphQueryService(make_graph())

    nodes = service.parents_of(
        "concept:brettanomyces"
    )

    assert [node.label for node in nodes] == [
        "Levure",
    ]


def test_children_of():
    service = GraphQueryService(make_graph())

    nodes = service.children_of(
        "concept:microorganism"
    )

    assert [node.label for node in nodes] == [
        "Levure",
    ]


def test_query_accepts_prefixed_document_id():
    service = GraphQueryService(make_graph())

    nodes = service.concepts_for_document(
        "document:NRIP-001"
    )

    assert [node.label for node in nodes] == [
        "Brettanomyces",
    ]


def test_query_accepts_unprefixed_concept_id():
    service = GraphQueryService(make_graph())

    nodes = service.documents_for_concept(
        "brettanomyces"
    )

    assert {
        node.node_id
        for node in nodes
    } == {
        "document:NRIP-001",
        "document:NRIP-002",
    }


def test_unknown_document_returns_empty_list():
    service = GraphQueryService(make_graph())

    assert (
        service.concepts_for_document("NRIP-999")
        == []
    )


def test_unknown_concept_returns_empty_list():
    service = GraphQueryService(make_graph())

    assert (
        service.documents_for_concept(
            "concept:unknown"
        )
        == []
    )


def test_empty_document_id_is_rejected():
    import pytest

    service = GraphQueryService(make_graph())

    with pytest.raises(ValueError):
        service.concepts_for_document("   ")


def test_empty_concept_id_is_rejected():
    import pytest

    service = GraphQueryService(make_graph())

    with pytest.raises(ValueError):
        service.parents_of("")


def test_invalid_graph_is_rejected():
    import pytest

    with pytest.raises(TypeError):
        GraphQueryService(None)
