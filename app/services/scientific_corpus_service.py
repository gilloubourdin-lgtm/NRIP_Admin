from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from app.models.knowledge_graph import KnowledgeGraph
from app.models.scientific_document import ScientificDocument
from app.services.document_parser import DocumentParser
from app.services.graph_builder import GraphBuilder
from app.services.knowledge_engine import KnowledgeEngine


@dataclass(slots=True)
class ScientificCorpus:
    documents: list[ScientificDocument]
    graph: KnowledgeGraph


class ScientificCorpusService:
    """
    Charge un corpus Markdown NRIP et construit
    son graphe scientifique deterministe.

    Les identifiants documentaires metier sont conserves.
    Les collisions sont desambiguees uniquement dans
    la representation technique du graphe.

    Aucun fait scientifique n'est invente.
    """

    def load(self, root: Path | str) -> ScientificCorpus:
        corpus_root = Path(root).expanduser().resolve()

        if not corpus_root.is_dir():
            raise ValueError(
                f"Invalid scientific corpus directory: {corpus_root}"
            )

        parser = DocumentParser()
        knowledge_engine = KnowledgeEngine()
        graph_builder = GraphBuilder()

        documents: list[ScientificDocument] = []

        for path in sorted(corpus_root.rglob("*.md")):
            if not path.is_file():
                continue

            document = parser.parse_file(
                path,
                root=corpus_root,
            )

            knowledge_engine.enrich(document)
            documents.append(document)

        counts = Counter(
            document.document_id
            for document in documents
        )

        duplicate_ids = {
            document_id
            for document_id, count in counts.items()
            if count > 1
        }

        if duplicate_ids:
            self._check_ambiguous_relations(
                documents,
                duplicate_ids,
            )

        # Prevent generated graph IDs from colliding with
        # existing scientific document identifiers.
        original_ids = set(counts)
        technical_ids: set[str] = set()

        for document in documents:
            if document.document_id not in duplicate_ids:
                continue

            technical_id = self._technical_document_id(
                document.document_id,
                document.relative_path,
            )

            if (
                technical_id in original_ids
                or technical_id in technical_ids
            ):
                raise ValueError(
                    "Collision d'identifiant technique : "
                    f"{technical_id!r}."
                )

            technical_ids.add(technical_id)

        graph_documents: list[ScientificDocument] = []

        for document in documents:
            if document.document_id not in duplicate_ids:
                graph_documents.append(document)
                continue

            graph_document = deepcopy(document)

            graph_document.document_id = (
                self._technical_document_id(
                    document.document_id,
                    document.relative_path,
                )
            )

            graph_documents.append(graph_document)

        graph = graph_builder.build(graph_documents)

        for document in documents:
            if document.document_id not in duplicate_ids:
                continue

            technical_id = self._technical_document_id(
                document.document_id,
                document.relative_path,
            )

            node = graph.nodes[f"document:{technical_id}"]

            node.metadata["document_id"] = document.document_id
            node.metadata["technical_document_id"] = technical_id

        return ScientificCorpus(
            documents=documents,
            graph=graph,
        )

    @staticmethod
    def _technical_document_id(
        document_id: str,
        relative_path: str,
    ) -> str:
        if not relative_path:
            raise ValueError(
                "Un document avec identifiant duplique "
                "doit avoir un chemin relatif."
            )

        return f"{document_id}@{relative_path}"

    @staticmethod
    def _check_ambiguous_relations(
        documents: list[ScientificDocument],
        duplicate_ids: set[str],
    ) -> None:
        for document in documents:
            for relation in document.relations:
                for endpoint in (
                    relation.source_id,
                    relation.target_id,
                ):
                    normalized = endpoint.removeprefix(
                        "document:"
                    )

                    if normalized in duplicate_ids:
                        raise ValueError(
                            "Relation documentaire ambiguë : "
                            f"{normalized!r}."
                        )
