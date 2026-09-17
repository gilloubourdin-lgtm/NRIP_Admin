from app.models.detected_entity import DetectedEntity
from app.models.scientific_document import ScientificDocument
from app.models.knowledge_graph import (
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
)
from app.services.graph_builder import GraphBuilder


def make_entity(
    *,
    start: int,
    end: int,
) -> DetectedEntity:
    return DetectedEntity(
        value="Brettanomyces",
        canonical="Brettanomyces",
        category="microorganism",
        taxonomy_id=(
            "organism.microorganism.yeast.brettanomyces"
        ),
        start=start,
        end=end,
    )


def test_graph_node_has_stable_identity():
    node = GraphNode(
        node_id="document:NRIP-001",
        node_type="document",
        label="Scientific document",
    )

    assert node.node_id == "document:NRIP-001"
    assert node.node_type == "document"
    assert node.label == "Scientific document"


def test_graph_edge_preserves_occurrences():
    first = make_entity(start=0, end=13)
    second = make_entity(start=30, end=43)

    edge = GraphEdge(
        source_id="document:NRIP-001",
        target_id=(
            "concept:"
            "organism.microorganism.yeast.brettanomyces"
        ),
        relation_type="mentions",
        occurrences=[first, second],
    )

    assert len(edge.occurrences) == 2


def test_knowledge_graph_deduplicates_nodes():
    graph = KnowledgeGraph()

    first = GraphNode(
        node_id="concept:test",
        node_type="concept",
        label="Test",
    )

    second = GraphNode(
        node_id="concept:test",
        node_type="concept",
        label="Test",
    )

    assert graph.add_node(first) is True
    assert graph.add_node(second) is False
    assert len(graph.nodes) == 1


def test_graph_builder_creates_document_and_concept_nodes():
    document = ScientificDocument(
        document_id="NRIP-001",
        title="Brettanomyces study",
        entities=[
            make_entity(start=0, end=13),
        ],
    )

    graph = GraphBuilder().build([document])

    assert "document:NRIP-001" in graph.nodes
    assert (
        "concept:"
        "organism.microorganism.yeast.brettanomyces"
        in graph.nodes
    )


def test_graph_builder_groups_occurrences_on_mentions_edge():
    document = ScientificDocument(
        document_id="NRIP-001",
        title="Repeated Brettanomyces",
        entities=[
            make_entity(start=0, end=13),
            make_entity(start=30, end=43),
        ],
    )

    graph = GraphBuilder().build([document])

    edge = graph.edges[
        (
            "document:NRIP-001:"
            "mentions:"
            "concept:"
            "organism.microorganism.yeast.brettanomyces"
        )
    ]

    assert len(edge.occurrences) == 2


def test_graph_builder_shares_concept_between_documents():
    first = ScientificDocument(
        document_id="NRIP-001",
        title="First document",
        entities=[
            make_entity(start=0, end=13),
        ],
    )

    second = ScientificDocument(
        document_id="NRIP-002",
        title="Second document",
        entities=[
            make_entity(start=10, end=23),
        ],
    )

    graph = GraphBuilder().build([first, second])

    concept_id = (
        "concept:"
        "organism.microorganism.yeast.brettanomyces"
    )

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


def test_graph_builder_rejects_invalid_document():
    builder = GraphBuilder()

    try:
        builder.build(["not a document"])
    except TypeError:
        pass
    else:
        raise AssertionError("TypeError expected")


def test_knowledge_graph_accepts_equivalent_duplicate_node():
    graph = KnowledgeGraph()

    first = GraphNode(
        node_id="concept:test",
        node_type="concept",
        label="Test",
        metadata={"category": "method"},
    )

    second = GraphNode(
        node_id="concept:test",
        node_type="concept",
        label="Test",
        metadata={"category": "method"},
    )

    assert graph.add_node(first) is True
    assert graph.add_node(second) is False
    assert graph.nodes["concept:test"] is first


def test_knowledge_graph_rejects_conflicting_duplicate_node():
    graph = KnowledgeGraph()

    graph.add_node(
        GraphNode(
            node_id="concept:test",
            node_type="concept",
            label="First concept",
        )
    )

    conflicting = GraphNode(
        node_id="concept:test",
        node_type="concept",
        label="Different concept",
    )

    try:
        graph.add_node(conflicting)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "ValueError expected for conflicting node identity"
        )


def test_graph_builder_adds_taxonomy_ancestors():
    document = ScientificDocument(
        document_id="NRIP-001",
        title="Brettanomyces study",
        entities=[
            make_entity(start=0, end=13),
        ],
    )

    graph = GraphBuilder().build([document])

    expected_nodes = {
        "concept:organism",
        "concept:organism.microorganism",
        "concept:organism.microorganism.yeast",
        (
            "concept:"
            "organism.microorganism.yeast.brettanomyces"
        ),
    }

    assert expected_nodes.issubset(graph.nodes)


def test_graph_builder_adds_taxonomy_is_a_edges():
    document = ScientificDocument(
        document_id="NRIP-001",
        title="Brettanomyces study",
        entities=[
            make_entity(start=0, end=13),
        ],
    )

    graph = GraphBuilder().build([document])

    expected_edges = {
        (
            "concept:"
            "organism.microorganism.yeast.brettanomyces:"
            "is_a:"
            "concept:organism.microorganism.yeast"
        ),
        (
            "concept:organism.microorganism.yeast:"
            "is_a:"
            "concept:organism.microorganism"
        ),
        (
            "concept:organism.microorganism:"
            "is_a:"
            "concept:organism"
        ),
    }

    assert expected_edges.issubset(graph.edges)


def test_graph_builder_does_not_create_is_a_for_root():
    document = ScientificDocument(
        document_id="NRIP-001",
        title="Wine study",
        plain_text="Le vin est étudié.",
    )

    from app.services.knowledge_engine import KnowledgeEngine

    KnowledgeEngine().enrich(document)

    graph = GraphBuilder().build([document])

    assert "concept:wine" in graph.nodes

    wine_edges = [
        edge
        for edge in graph.edges.values()
        if (
            edge.source_id == "concept:wine"
            and edge.relation_type == "is_a"
        )
    ]

    assert wine_edges == []
