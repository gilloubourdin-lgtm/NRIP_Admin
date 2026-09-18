from __future__ import annotations

from collections.abc import Iterable

from app.models.document_relation import DocumentRelation
from app.models.knowledge_graph import (
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
)
from app.models.scientific_document import ScientificDocument
from app.services.taxonomy import TaxonomyEngine


class GraphBuilder:
    """
    Construit le Knowledge Graph depuis des documents enrichis.

    V2 :
        document -> noeud document
        entite -> noeud concept canonique
        document -> mentions -> concept
        concept -> is_a -> parent taxonomique

    Les occurrences restent attachees aux aretes mentions.
    Les relations is_a proviennent de la taxonomie.
    """

    def __init__(
        self,
        *,
        taxonomy: TaxonomyEngine | None = None,
    ) -> None:
        self.taxonomy = (
            taxonomy
            if taxonomy is not None
            else TaxonomyEngine()
        )

    def build(
        self,
        documents: Iterable[ScientificDocument],
    ) -> KnowledgeGraph:
        graph = KnowledgeGraph()

        document_list = list(documents)

        for document in document_list:
            if not isinstance(document, ScientificDocument):
                raise TypeError(
                    "Tous les elements doivent etre "
                    "des ScientificDocument."
                )

            document_node_id = (
                f"document:{document.document_id}"
            )

            graph.add_node(
                GraphNode(
                    node_id=document_node_id,
                    node_type="document",
                    label=document.title,
                    metadata={
                        "document_id": document.document_id,
                        "document_type": document.document_type,
                        "relative_path": document.relative_path,
                    },
                )
            )

            for entity in document.entities:
                concept_node_id = (
                    f"concept:{entity.normalized_key}"
                )

                graph.add_node(
                    GraphNode(
                        node_id=concept_node_id,
                        node_type="concept",
                        label=entity.canonical,
                        metadata={
                            "category": entity.category,
                            "taxonomy_id": entity.taxonomy_id,
                        },
                    )
                )

                graph.add_edge(
                    GraphEdge(
                        source_id=document_node_id,
                        target_id=concept_node_id,
                        relation_type="mentions",
                        occurrences=[entity],
                    )
                )

                self._add_taxonomy_path(
                    graph=graph,
                    taxonomy_id=entity.taxonomy_id,
                )

        for document in document_list:
            for relation in document.relations:
                self._add_document_relation(
                    graph=graph,
                    relation=relation,
                )

        return graph

    def _add_document_relation(
        self,
        *,
        graph: KnowledgeGraph,
        relation: DocumentRelation,
    ) -> None:
        source_id = self._resolve_relation_node_id(
            graph=graph,
            value=relation.source_id,
        )
        target_id = self._resolve_relation_node_id(
            graph=graph,
            value=relation.target_id,
        )

        if source_id is None or target_id is None:
            return

        metadata = {
            "confidence": relation.confidence,
            "source_line": relation.source_line,
            "source_text": relation.source_text,
            "created_by": relation.created_by,
            "bidirectional": relation.bidirectional,
        }

        graph.add_edge(
            GraphEdge(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation.relation_type,
                metadata=metadata,
            )
        )

        if relation.bidirectional:
            graph.add_edge(
                GraphEdge(
                    source_id=target_id,
                    target_id=source_id,
                    relation_type=relation.relation_type,
                    metadata=dict(metadata),
                )
            )

    def _resolve_relation_node_id(
        self,
        *,
        graph: KnowledgeGraph,
        value: str,
    ) -> str | None:
        if value.startswith("document:"):
            candidate = value
        elif value.startswith("concept:"):
            candidate = value
        else:
            document_candidate = (
                f"document:{value}"
            )

            if document_candidate in graph.nodes:
                return document_candidate

            taxonomy_node = self.taxonomy.find(
                value
            )

            if taxonomy_node is None:
                return None

            candidate = (
                f"concept:{taxonomy_node.id}"
            )

        if candidate not in graph.nodes:
            return None

        return candidate

    def _add_taxonomy_path(
        self,
        *,
        graph: KnowledgeGraph,
        taxonomy_id: str | None,
    ) -> None:
        if not taxonomy_id:
            return

        node = self.taxonomy.find(taxonomy_id)

        if node is None:
            return

        path = self.taxonomy.path(node)

        for taxonomy_node in path:
            graph.add_node(
                GraphNode(
                    node_id=f"concept:{taxonomy_node.id}",
                    node_type="concept",
                    label=taxonomy_node.name,
                    metadata={
                        "category": taxonomy_node.category,
                        "taxonomy_id": taxonomy_node.id,
                        "parent_id": taxonomy_node.parent_id,
                    },
                )
            )

        for child, parent in zip(
            reversed(path[1:]),
            reversed(path[:-1]),
        ):
            graph.add_edge(
                GraphEdge(
                    source_id=f"concept:{child.id}",
                    target_id=f"concept:{parent.id}",
                    relation_type="is_a",
                )
            )
