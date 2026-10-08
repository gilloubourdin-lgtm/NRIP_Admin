from __future__ import annotations

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

        graph = graph_builder.build(documents)

        return ScientificCorpus(
            documents=documents,
            graph=graph,
        )
