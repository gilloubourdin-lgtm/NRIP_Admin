from __future__ import annotations

from app.models.knowledge_graph import (
    GraphEdge,
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

    def outgoing_relations(
        self,
        node_id: str,
        relation_type: str | None = None,
    ) -> list[GraphEdge]:
        node_id = self._graph_node_id(node_id)
        relation_type = self._relation_type(
            relation_type
        )

        if node_id not in self.graph.nodes:
            return []

        return [
            edge
            for edge in self.graph.edges.values()
            if (
                edge.source_id == node_id
                and (
                    relation_type is None
                    or edge.relation_type
                    == relation_type
                )
            )
        ]

    def incoming_relations(
        self,
        node_id: str,
        relation_type: str | None = None,
    ) -> list[GraphEdge]:
        node_id = self._graph_node_id(node_id)
        relation_type = self._relation_type(
            relation_type
        )

        if node_id not in self.graph.nodes:
            return []

        return [
            edge
            for edge in self.graph.edges.values()
            if (
                edge.target_id == node_id
                and (
                    relation_type is None
                    or edge.relation_type
                    == relation_type
                )
            )
        ]

    def documents_matching_relations(
        self,
        constraints: list[tuple[str, str]],
    ) -> list[GraphNode]:
        """
        Retourne les documents satisfaisant toutes
        les contraintes relationnelles.

        Chaque contrainte est un tuple :
            (relation_type, concept_id)

        La combinaison applique une semantique AND.
        """

        if not isinstance(constraints, list):
            raise TypeError(
                "constraints doit etre une liste."
            )

        if not constraints:
            return []

        matching_document_ids: (
            set[str] | None
        ) = None

        for constraint in constraints:
            if (
                not isinstance(constraint, tuple)
                or len(constraint) != 2
            ):
                raise TypeError(
                    "Chaque contrainte doit etre "
                    "un tuple (relation_type, concept_id)."
                )

            relation_type, concept_id = constraint

            relation_type = self._relation_type(
                relation_type
            )
            concept_node_id = self._concept_node_id(
                concept_id
            )

            edges = self.incoming_relations(
                concept_node_id,
                relation_type=relation_type,
            )

            document_ids = {
                edge.source_id
                for edge in edges
                if (
                    edge.source_id in self.graph.nodes
                    and self.graph.nodes[
                        edge.source_id
                    ].node_type == "document"
                )
            }

            if matching_document_ids is None:
                matching_document_ids = document_ids
            else:
                matching_document_ids &= document_ids

            if not matching_document_ids:
                return []

        if matching_document_ids is None:
            return []

        return [
            node
            for node in self.graph.nodes.values()
            if (
                node.node_type == "document"
                and node.node_id
                in matching_document_ids
            )
        ]

    def documents_matching_relation_families(
        self,
        constraints: list[tuple[str, str]],
    ) -> list[GraphNode]:
        """
        Retourne les documents satisfaisant toutes
        les contraintes relationnelles en incluant
        les descendants taxonomiques des concepts.

        Chaque contrainte est un tuple :
            (relation_type, concept_id)

        Les concepts d'une meme famille sont combines
        avec une semantique OR. Les contraintes entre
        elles utilisent une semantique AND.
        """

        if not isinstance(constraints, list):
            raise TypeError(
                "constraints doit etre une liste."
            )

        if not constraints:
            return []

        matching_document_ids: (
            set[str] | None
        ) = None

        for constraint in constraints:
            if (
                not isinstance(constraint, tuple)
                or len(constraint) != 2
            ):
                raise TypeError(
                    "Chaque contrainte doit etre "
                    "un tuple (relation_type, concept_id)."
                )

            relation_type, concept_id = constraint

            relation_type = self._relation_type(
                relation_type
            )
            concept_node_id = self._concept_node_id(
                concept_id
            )

            concept_nodes = (
                [self.graph.nodes[concept_node_id]]
                if concept_node_id in self.graph.nodes
                else []
            )

            concept_nodes.extend(
                self.descendants_of(
                    concept_node_id
                )
            )

            document_ids: set[str] = set()

            for concept_node in concept_nodes:
                edges = self.incoming_relations(
                    concept_node.node_id,
                    relation_type=relation_type,
                )

                document_ids.update(
                    edge.source_id
                    for edge in edges
                    if (
                        edge.source_id
                        in self.graph.nodes
                        and self.graph.nodes[
                            edge.source_id
                        ].node_type == "document"
                    )
                )

            if matching_document_ids is None:
                matching_document_ids = document_ids
            else:
                matching_document_ids &= document_ids

            if not matching_document_ids:
                return []

        if matching_document_ids is None:
            return []

        return [
            node
            for node in self.graph.nodes.values()
            if (
                node.node_type == "document"
                and node.node_id
                in matching_document_ids
            )
        ]

    def methods_for_document(
        self,
        document_id: str,
    ) -> list[GraphNode]:
        document_node_id = self._document_node_id(
            document_id
        )

        return self._target_nodes_for_relations(
            self.outgoing_relations(
                document_node_id,
                relation_type="uses_method",
            ),
            node_type="concept",
        )

    def concepts_studied_by_document(
        self,
        document_id: str,
    ) -> list[GraphNode]:
        document_node_id = self._document_node_id(
            document_id
        )

        return self._target_nodes_for_relations(
            self.outgoing_relations(
                document_node_id,
                relation_type="studies",
            ),
            node_type="concept",
        )

    def documents_using_method(
        self,
        concept_id: str,
    ) -> list[GraphNode]:
        concept_node_id = self._concept_node_id(
            concept_id
        )

        return self._source_nodes_for_relations(
            self.incoming_relations(
                concept_node_id,
                relation_type="uses_method",
            ),
            node_type="document",
        )

    def documents_studying_concept(
        self,
        concept_id: str,
    ) -> list[GraphNode]:
        concept_node_id = self._concept_node_id(
            concept_id
        )

        return self._source_nodes_for_relations(
            self.incoming_relations(
                concept_node_id,
                relation_type="studies",
            ),
            node_type="document",
        )

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

    def documents_for_concept_family(
        self,
        concept_id: str,
    ) -> list[GraphNode]:
        concept_node_id = self._concept_node_id(
            concept_id
        )

        concept_nodes = [
            self.graph.nodes.get(concept_node_id),
            *self.descendants_of(concept_node_id),
        ]

        documents: list[GraphNode] = []
        seen_document_ids: set[str] = set()

        for concept_node in concept_nodes:
            if concept_node is None:
                continue

            for document in self.documents_for_concept(
                concept_node.node_id
            ):
                if document.node_id in seen_document_ids:
                    continue

                seen_document_ids.add(document.node_id)
                documents.append(document)

        return documents

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

    def ancestors_of(
        self,
        concept_id: str,
    ) -> list[GraphNode]:
        concept_node_id = self._concept_node_id(
            concept_id
        )

        return self._traverse(
            start_id=concept_node_id,
            direction="targets",
        )

    def descendants_of(
        self,
        concept_id: str,
    ) -> list[GraphNode]:
        concept_node_id = self._concept_node_id(
            concept_id
        )

        return self._traverse(
            start_id=concept_node_id,
            direction="sources",
        )

    def _target_nodes_for_relations(
        self,
        edges: list[GraphEdge],
        *,
        node_type: str,
    ) -> list[GraphNode]:
        nodes: list[GraphNode] = []

        for edge in edges:
            node = self.graph.nodes.get(
                edge.target_id
            )

            if (
                node is not None
                and node.node_type == node_type
            ):
                nodes.append(node)

        return nodes

    def _source_nodes_for_relations(
        self,
        edges: list[GraphEdge],
        *,
        node_type: str,
    ) -> list[GraphNode]:
        nodes: list[GraphNode] = []

        for edge in edges:
            node = self.graph.nodes.get(
                edge.source_id
            )

            if (
                node is not None
                and node.node_type == node_type
            ):
                nodes.append(node)

        return nodes

    def _traverse(
        self,
        *,
        start_id: str,
        direction: str,
    ) -> list[GraphNode]:
        visited = {start_id}
        queue = [start_id]
        result: list[GraphNode] = []

        while queue:
            current_id = queue.pop(0)

            if direction == "targets":
                neighbours = self._targets(
                    source_id=current_id,
                    relation_type="is_a",
                    node_type="concept",
                )
            elif direction == "sources":
                neighbours = self._sources(
                    target_id=current_id,
                    relation_type="is_a",
                    node_type="concept",
                )
            else:
                raise ValueError(
                    "direction de parcours invalide."
                )

            for node in neighbours:
                if node.node_id in visited:
                    continue

                visited.add(node.node_id)
                result.append(node)
                queue.append(node.node_id)

        return result

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
    def _graph_node_id(
        node_id: str,
    ) -> str:
        if not isinstance(node_id, str):
            raise TypeError(
                "node_id doit etre une chaine."
            )

        value = node_id.strip()

        if not value:
            raise ValueError(
                "node_id ne peut pas etre vide."
            )

        return value

    @staticmethod
    def _relation_type(
        relation_type: str | None,
    ) -> str | None:
        if relation_type is None:
            return None

        if not isinstance(relation_type, str):
            raise TypeError(
                "relation_type doit etre une chaine "
                "ou None."
            )

        value = relation_type.strip().lower()

        if not value:
            raise ValueError(
                "relation_type ne peut pas etre vide."
            )

        return value

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
