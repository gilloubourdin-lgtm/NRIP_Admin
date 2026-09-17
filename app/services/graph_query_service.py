from __future__ import annotations

from app.models.knowledge_graph import (
    GraphNode,
    KnowledgeGraph,
)


class GraphQueryService:
    """
    Service de lecture du Knowledge Graph NRIP.

    V1 :
        document -> concepts mentionnes
        concept -> documents qui le mentionnent
        concept -> parents taxonomiques directs
        concept -> enfants taxonomiques directs
    """

    def __init__(
        self,
        graph: KnowledgeGraph,
    ) -> None:
        if not isinstance(graph, KnowledgeGraph):
            raise TypeError(
                "graph doit etre un KnowledgeGraph."
            )

        self.graph = graph

    def concepts_for_document(
        self,
        document_id: str,
    ) -> list[GraphNode]:
        document_node_id = self._document_node_id(
            document_id
        )

        return self._targets(
            source_id=document_node_id,
            relation_type="mentions",
            node_type="concept",
        )

    def documents_for_concept(
        self,
        concept_id: str,
    ) -> list[GraphNode]:
        concept_node_id = self._concept_node_id(
            concept_id
        )

        return self._sources(
            target_id=concept_node_id,
            relation_type="mentions",
            node_type="document",
        )

    def parents_of(
        self,
        concept_id: str,
    ) -> list[GraphNode]:
        concept_node_id = self._concept_node_id(
            concept_id
        )

        return self._targets(
            source_id=concept_node_id,
            relation_type="is_a",
            node_type="concept",
        )

    def children_of(
        self,
        concept_id: str,
    ) -> list[GraphNode]:
        concept_node_id = self._concept_node_id(
            concept_id
        )

        return self._sources(
            target_id=concept_node_id,
            relation_type="is_a",
            node_type="concept",
        )

    def _targets(
        self,
        *,
        source_id: str,
        relation_type: str,
        node_type: str,
    ) -> list[GraphNode]:
        nodes: list[GraphNode] = []

        for edge in self.graph.edges.values():
            if (
                edge.source_id != source_id
                or edge.relation_type != relation_type
            ):
                continue

            node = self.graph.nodes.get(
                edge.target_id
            )

            if (
                node is not None
                and node.node_type == node_type
            ):
                nodes.append(node)

        return nodes

    def _sources(
        self,
        *,
        target_id: str,
        relation_type: str,
        node_type: str,
    ) -> list[GraphNode]:
        nodes: list[GraphNode] = []

        for edge in self.graph.edges.values():
            if (
                edge.target_id != target_id
                or edge.relation_type != relation_type
            ):
                continue

            node = self.graph.nodes.get(
                edge.source_id
            )

            if (
                node is not None
                and node.node_type == node_type
            ):
                nodes.append(node)

        return nodes

    @staticmethod
    def _document_node_id(
        document_id: str,
    ) -> str:
        if not isinstance(document_id, str):
            raise TypeError(
                "document_id doit etre une chaine."
            )

        value = document_id.strip()

        if not value:
            raise ValueError(
                "document_id ne peut pas etre vide."
            )

        if value.startswith("document:"):
            return value

        return f"document:{value}"

    @staticmethod
    def _concept_node_id(
        concept_id: str,
    ) -> str:
        if not isinstance(concept_id, str):
            raise TypeError(
                "concept_id doit etre une chaine."
            )

        value = concept_id.strip()

        if not value:
            raise ValueError(
                "concept_id ne peut pas etre vide."
            )

        if value.startswith("concept:"):
            return value

        return f"concept:{value}"
