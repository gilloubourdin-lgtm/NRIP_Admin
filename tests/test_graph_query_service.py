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


def test_ancestors_of_returns_full_hierarchy():
    service = GraphQueryService(make_graph())

    nodes = service.ancestors_of(
        "concept:brettanomyces"
    )

    assert [
        node.label
        for node in nodes
    ] == [
        "Levure",
        "Microorganisme",
    ]


def test_descendants_of_returns_full_hierarchy():
    service = GraphQueryService(make_graph())

    nodes = service.descendants_of(
        "concept:microorganism"
    )

    assert [
        node.label
        for node in nodes
    ] == [
        "Levure",
        "Brettanomyces",
    ]


def test_transitive_queries_do_not_duplicate_nodes():
    graph = make_graph()

    graph.add_edge(
        GraphEdge(
            source_id="concept:brettanomyces",
            target_id="concept:microorganism",
            relation_type="is_a",
        )
    )

    service = GraphQueryService(graph)

    ancestors = service.ancestors_of(
        "concept:brettanomyces"
    )

    assert [
        node.node_id
        for node in ancestors
    ] == [
        "concept:yeast",
        "concept:microorganism",
    ]


def test_transitive_queries_are_cycle_safe():
    graph = make_graph()

    graph.add_edge(
        GraphEdge(
            source_id="concept:microorganism",
            target_id="concept:brettanomyces",
            relation_type="is_a",
        )
    )

    service = GraphQueryService(graph)

    ancestors = service.ancestors_of(
        "concept:brettanomyces"
    )

    assert {
        node.node_id
        for node in ancestors
    } == {
        "concept:yeast",
        "concept:microorganism",
    }

    assert all(
        node.node_id != "concept:brettanomyces"
        for node in ancestors
    )


def test_documents_for_concept_family_includes_descendants():
    service = GraphQueryService(make_graph())

    nodes = service.documents_for_concept_family(
        "concept:microorganism"
    )

    assert {
        node.node_id
        for node in nodes
    } == {
        "document:NRIP-001",
        "document:NRIP-002",
    }


def test_documents_for_concept_family_includes_root_concept():
    graph = make_graph()

    graph.add_edge(
        GraphEdge(
            source_id="document:NRIP-001",
            target_id="concept:microorganism",
            relation_type="mentions",
        )
    )

    service = GraphQueryService(graph)

    nodes = service.documents_for_concept_family(
        "concept:microorganism"
    )

    assert {
        node.node_id
        for node in nodes
    } == {
        "document:NRIP-001",
        "document:NRIP-002",
    }


def test_documents_for_concept_family_deduplicates_documents():
    graph = make_graph()

    graph.add_edge(
        GraphEdge(
            source_id="document:NRIP-001",
            target_id="concept:yeast",
            relation_type="mentions",
        )
    )

    service = GraphQueryService(graph)

    nodes = service.documents_for_concept_family(
        "microorganism"
    )

    assert [
        node.node_id
        for node in nodes
    ].count(
        "document:NRIP-001"
    ) == 1

    assert {
        node.node_id
        for node in nodes
    } == {
        "document:NRIP-001",
        "document:NRIP-002",
    }


def make_scientific_relation_graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()

    nodes = [
        GraphNode(
            node_id="document:NRIP-REL-001",
            node_type="document",
            label="Scientific study",
        ),
        GraphNode(
            node_id="concept:gc_ms",
            node_type="concept",
            label="GC-MS",
        ),
        GraphNode(
            node_id="concept:brettanomyces",
            node_type="concept",
            label="Brettanomyces",
        ),
    ]

    for node in nodes:
        graph.add_node(node)

    graph.add_edge(
        GraphEdge(
            source_id="document:NRIP-REL-001",
            target_id="concept:gc_ms",
            relation_type="uses_method",
            metadata={
                "confidence": 0.95,
                "source_line": 12,
                "source_text": "Analysis by GC-MS.",
                "created_by": "curator",
            },
        )
    )

    graph.add_edge(
        GraphEdge(
            source_id="document:NRIP-REL-001",
            target_id="concept:brettanomyces",
            relation_type="studies",
            metadata={
                "confidence": 0.90,
                "source_line": 8,
                "source_text": "Brettanomyces was studied.",
                "created_by": "curator",
            },
        )
    )

    return graph


def test_outgoing_relations_returns_scientific_edges():
    service = GraphQueryService(
        make_scientific_relation_graph()
    )

    edges = service.outgoing_relations(
        "document:NRIP-REL-001"
    )

    assert [
        edge.relation_type
        for edge in edges
    ] == [
        "uses_method",
        "studies",
    ]


def test_outgoing_relations_filters_relation_type():
    service = GraphQueryService(
        make_scientific_relation_graph()
    )

    edges = service.outgoing_relations(
        "document:NRIP-REL-001",
        relation_type="uses_method",
    )

    assert len(edges) == 1
    assert edges[0].target_id == "concept:gc_ms"


def test_incoming_relations_returns_scientific_edges():
    service = GraphQueryService(
        make_scientific_relation_graph()
    )

    edges = service.incoming_relations(
        "concept:gc_ms"
    )

    assert len(edges) == 1
    assert edges[0].source_id == (
        "document:NRIP-REL-001"
    )
    assert edges[0].relation_type == "uses_method"


def test_relation_queries_preserve_metadata():
    service = GraphQueryService(
        make_scientific_relation_graph()
    )

    edge = service.outgoing_relations(
        "document:NRIP-REL-001",
        relation_type="uses_method",
    )[0]

    assert edge.metadata["confidence"] == 0.95
    assert edge.metadata["source_line"] == 12
    assert edge.metadata["source_text"] == (
        "Analysis by GC-MS."
    )
    assert edge.metadata["created_by"] == "curator"


def test_relation_queries_unknown_node_return_empty_list():
    service = GraphQueryService(
        make_scientific_relation_graph()
    )

    assert service.outgoing_relations(
        "document:UNKNOWN"
    ) == []

    assert service.incoming_relations(
        "concept:unknown"
    ) == []


def test_relation_queries_reject_empty_node_id():
    import pytest

    service = GraphQueryService(
        make_scientific_relation_graph()
    )

    with pytest.raises(ValueError):
        service.outgoing_relations("   ")

    with pytest.raises(ValueError):
        service.incoming_relations("")


def test_relation_type_is_normalized():
    service = GraphQueryService(
        make_scientific_relation_graph()
    )

    edges = service.outgoing_relations(
        "document:NRIP-REL-001",
        relation_type="  USES_METHOD  ",
    )

    assert len(edges) == 1
    assert edges[0].relation_type == "uses_method"


def test_relation_type_rejects_invalid_value():
    import pytest

    service = GraphQueryService(
        make_scientific_relation_graph()
    )

    with pytest.raises(TypeError):
        service.outgoing_relations(
            "document:NRIP-REL-001",
            relation_type=123,
        )

    with pytest.raises(ValueError):
        service.outgoing_relations(
            "document:NRIP-REL-001",
            relation_type="   ",
        )


def test_scientific_relation_query_real_pipeline():
    from app.models.detected_entity import DetectedEntity
    from app.models.document_relation import DocumentRelation
    from app.models.scientific_document import ScientificDocument
    from app.services.graph_builder import GraphBuilder

    document = ScientificDocument(
        document_id="NRIP-REL-PIPELINE",
        title="GC-MS analysis",
        entities=[
            DetectedEntity(
                value="GC-MS",
                canonical="GC-MS",
                category="analytical_method",
                taxonomy_id=(
                    "analysis.chromatography.gc_ms"
                ),
                start=0,
                end=5,
            )
        ],
        relations=[
            DocumentRelation(
                source_id="NRIP-REL-PIPELINE",
                target_id=(
                    "analysis.chromatography.gc_ms"
                ),
                relation_type="uses_method",
                confidence=0.97,
                source_line=4,
                source_text=(
                    "Samples were analysed by GC-MS."
                ),
                created_by="curator",
            )
        ],
    )

    graph = GraphBuilder().build([document])
    service = GraphQueryService(graph)

    outgoing = service.outgoing_relations(
        "document:NRIP-REL-PIPELINE",
        relation_type="uses_method",
    )

    assert len(outgoing) == 1

    edge = outgoing[0]

    assert edge.target_id == (
        "concept:analysis.chromatography.gc_ms"
    )
    assert edge.metadata["confidence"] == 0.97
    assert edge.metadata["source_line"] == 4
    assert edge.metadata["source_text"] == (
        "Samples were analysed by GC-MS."
    )

    incoming = service.incoming_relations(
        "concept:analysis.chromatography.gc_ms",
        relation_type="uses_method",
    )

    assert len(incoming) == 1
    assert incoming[0] is edge


def test_methods_for_document():
    service = GraphQueryService(
        make_scientific_relation_graph()
    )

    nodes = service.methods_for_document(
        "NRIP-REL-001"
    )

    assert [
        node.node_id
        for node in nodes
    ] == [
        "concept:gc_ms",
    ]


def test_concepts_studied_by_document():
    service = GraphQueryService(
        make_scientific_relation_graph()
    )

    nodes = service.concepts_studied_by_document(
        "document:NRIP-REL-001"
    )

    assert [
        node.node_id
        for node in nodes
    ] == [
        "concept:brettanomyces",
    ]


def test_documents_using_method():
    service = GraphQueryService(
        make_scientific_relation_graph()
    )

    nodes = service.documents_using_method(
        "gc_ms"
    )

    assert [
        node.node_id
        for node in nodes
    ] == [
        "document:NRIP-REL-001",
    ]


def test_documents_studying_concept():
    service = GraphQueryService(
        make_scientific_relation_graph()
    )

    nodes = service.documents_studying_concept(
        "concept:brettanomyces"
    )

    assert [
        node.node_id
        for node in nodes
    ] == [
        "document:NRIP-REL-001",
    ]


def test_scientific_business_queries_do_not_use_mentions():
    graph = make_scientific_relation_graph()

    graph.add_edge(
        GraphEdge(
            source_id="document:NRIP-002",
            target_id="concept:gc_ms",
            relation_type="mentions",
        )
    )

    service = GraphQueryService(graph)

    documents = service.documents_using_method(
        "gc_ms"
    )

    assert [
        node.node_id
        for node in documents
    ] == [
        "document:NRIP-REL-001",
    ]


def test_scientific_business_queries_real_pipeline():
    from app.models.detected_entity import DetectedEntity
    from app.models.document_relation import DocumentRelation
    from app.models.scientific_document import ScientificDocument
    from app.services.graph_builder import GraphBuilder

    document = ScientificDocument(
        document_id="NRIP-SCIENCE-PIPELINE",
        title="Brettanomyces GC-MS study",
        entities=[
            DetectedEntity(
                value="Brettanomyces",
                canonical="Brettanomyces",
                category="microorganism",
                taxonomy_id=(
                    "organism.microorganism."
                    "yeast.brettanomyces"
                ),
                start=0,
                end=13,
            ),
            DetectedEntity(
                value="GC-MS",
                canonical="GC-MS",
                category="analytical_method",
                taxonomy_id=(
                    "analysis.chromatography.gc_ms"
                ),
                start=20,
                end=25,
            ),
        ],
        relations=[
            DocumentRelation(
                source_id="NRIP-SCIENCE-PIPELINE",
                target_id=(
                    "organism.microorganism."
                    "yeast.brettanomyces"
                ),
                relation_type="studies",
                confidence=0.94,
                source_line=3,
                source_text=(
                    "Brettanomyces was analysed by GC-MS."
                ),
                created_by="curator",
            ),
            DocumentRelation(
                source_id="NRIP-SCIENCE-PIPELINE",
                target_id=(
                    "analysis.chromatography.gc_ms"
                ),
                relation_type="uses_method",
                confidence=0.98,
                source_line=3,
                source_text=(
                    "Brettanomyces was analysed by GC-MS."
                ),
                created_by="curator",
            ),
        ],
    )

    graph = GraphBuilder().build([document])
    service = GraphQueryService(graph)

    methods = service.methods_for_document(
        "NRIP-SCIENCE-PIPELINE"
    )
    studied = service.concepts_studied_by_document(
        "NRIP-SCIENCE-PIPELINE"
    )
    method_documents = service.documents_using_method(
        "analysis.chromatography.gc_ms"
    )
    study_documents = service.documents_studying_concept(
        (
            "organism.microorganism."
            "yeast.brettanomyces"
        )
    )

    assert [
        node.node_id
        for node in methods
    ] == [
        "concept:analysis.chromatography.gc_ms",
    ]

    assert [
        node.node_id
        for node in studied
    ] == [
        (
            "concept:organism.microorganism."
            "yeast.brettanomyces"
        ),
    ]

    assert [
        node.node_id
        for node in method_documents
    ] == [
        "document:NRIP-SCIENCE-PIPELINE",
    ]

    assert [
        node.node_id
        for node in study_documents
    ] == [
        "document:NRIP-SCIENCE-PIPELINE",
    ]

    uses_method = service.outgoing_relations(
        "document:NRIP-SCIENCE-PIPELINE",
        relation_type="uses_method",
    )[0]

    studies = service.outgoing_relations(
        "document:NRIP-SCIENCE-PIPELINE",
        relation_type="studies",
    )[0]

    assert uses_method.metadata["confidence"] == 0.98
    assert studies.metadata["confidence"] == 0.94
    assert uses_method.metadata["source_line"] == 3
    assert studies.metadata["source_line"] == 3
