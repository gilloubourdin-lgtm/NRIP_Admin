from app.models.document_relation import DocumentRelation
from app.models.scientific_document import ScientificDocument
from app.services.assistant_engine import AssistantEngine
from app.services.graph_builder import GraphBuilder
from app.services.graph_query_service import GraphQueryService
from app.services.knowledge_engine import KnowledgeEngine


def test_scientific_relation_pipeline_end_to_end():
    text = (
        "Brettanomyces est analyse par GC-MS."
    )

    document = ScientificDocument(
        document_id="NRIP-RELATION-E2E",
        title="Scientific relation pipeline",
        plain_text=text,
    )

    # 1. Extraction deterministe des concepts
    KnowledgeEngine().enrich(document)

    canonical = {
        entity.canonical
        for entity in document.entities
    }

    assert "Brettanomyces" in canonical
    assert "GC-MS" in canonical

    # 2. Relations scientifiques explicites
    document.add_relation(
        DocumentRelation(
            source_id="NRIP-RELATION-E2E",
            target_id=(
                "organism.microorganism."
                "yeast.brettanomyces"
            ),
            relation_type="studies",
            confidence=0.95,
            source_line=1,
            source_text=text,
            created_by="curator",
        )
    )

    document.add_relation(
        DocumentRelation(
            source_id="NRIP-RELATION-E2E",
            target_id=(
                "analysis.chromatography.gc_ms"
            ),
            relation_type="uses_method",
            confidence=0.98,
            source_line=1,
            source_text=text,
            created_by="curator",
        )
    )

    # 3. Construction du Knowledge Graph
    graph = GraphBuilder().build([document])

    document_node_id = (
        "document:NRIP-RELATION-E2E"
    )
    brett_node_id = (
        "concept:"
        "organism.microorganism."
        "yeast.brettanomyces"
    )
    gcms_node_id = (
        "concept:"
        "analysis.chromatography.gc_ms"
    )

    assert document_node_id in graph.nodes
    assert brett_node_id in graph.nodes
    assert gcms_node_id in graph.nodes

    # Les occurrences lexicales restent distinctes
    # des relations scientifiques.
    assert (
        f"{document_node_id}:mentions:{brett_node_id}"
        in graph.edges
    )
    assert (
        f"{document_node_id}:mentions:{gcms_node_id}"
        in graph.edges
    )
    assert (
        f"{document_node_id}:studies:{brett_node_id}"
        in graph.edges
    )
    assert (
        f"{document_node_id}:uses_method:{gcms_node_id}"
        in graph.edges
    )

    # 4. Interrogation scientifique du graphe
    queries = GraphQueryService(graph)

    studied = queries.concepts_studied_by_document(
        "NRIP-RELATION-E2E"
    )
    methods = queries.methods_for_document(
        "NRIP-RELATION-E2E"
    )

    assert [
        node.node_id
        for node in studied
    ] == [
        brett_node_id,
    ]

    assert [
        node.node_id
        for node in methods
    ] == [
        gcms_node_id,
    ]

    assert [
        node.node_id
        for node in queries.documents_studying_concept(
            "organism.microorganism."
            "yeast.brettanomyces"
        )
    ] == [
        document_node_id,
    ]

    assert [
        node.node_id
        for node in queries.documents_using_method(
            "analysis.chromatography.gc_ms"
        )
    ] == [
        document_node_id,
    ]

    # 5. Assistant : preuve lexicale + relationnelle
    assistant = AssistantEngine(graph=graph)

    brett_result = assistant.lookup(
        "Brettanomyces"
    )
    gcms_result = assistant.lookup(
        "GC-MS"
    )

    assert brett_result.found is True
    assert gcms_result.found is True

    assert len(brett_result.evidence) == 1
    assert len(gcms_result.evidence) == 1

    assert len(
        brett_result.relation_evidence
    ) == 1
    assert len(
        gcms_result.relation_evidence
    ) == 1

    brett_relation = (
        brett_result.relation_evidence[0]
        .relation
    )
    gcms_relation = (
        gcms_result.relation_evidence[0]
        .relation
    )

    assert brett_relation.relation_type == (
        "studies"
    )
    assert gcms_relation.relation_type == (
        "uses_method"
    )

    # 6. Provenance preservee jusqu'a l'assistant
    assert brett_relation.metadata[
        "confidence"
    ] == 0.95
    assert gcms_relation.metadata[
        "confidence"
    ] == 0.98

    assert brett_relation.metadata[
        "source_line"
    ] == 1
    assert gcms_relation.metadata[
        "source_line"
    ] == 1

    assert brett_relation.metadata[
        "source_text"
    ] == text
    assert gcms_relation.metadata[
        "source_text"
    ] == text

    assert brett_relation.metadata[
        "created_by"
    ] == "curator"
    assert gcms_relation.metadata[
        "created_by"
    ] == "curator"

    # La preuve lexicale conserve aussi ses offsets.
    brett_occurrence = (
        brett_result.evidence[0].occurrence
    )
    gcms_occurrence = (
        gcms_result.evidence[0].occurrence
    )

    assert text[
        brett_occurrence.start:
        brett_occurrence.end
    ] == "Brettanomyces"

    assert text[
        gcms_occurrence.start:
        gcms_occurrence.end
    ] == "GC-MS"
