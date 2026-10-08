from __future__ import annotations

from pathlib import Path

from app.services.assistant_engine import (
    AssistantEngine,
    AssistantResult,
)
from app.services.scientific_corpus_service import (
    ScientificCorpusService,
)


class ScientificSearchService:
    """
    Recherche deterministe de concepts dans un corpus NRIP.

    Les resultats proviennent exclusivement du graphe
    scientifique construit a partir des documents.
    """

    def search(
        self,
        *,
        root: Path | str,
        query: str,
    ) -> AssistantResult:
        if not isinstance(query, str):
            raise TypeError(
                "query doit etre une chaine."
            )

        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError(
                "query ne peut pas etre vide."
            )

        corpus = ScientificCorpusService().load(root)

        assistant = AssistantEngine(
            graph=corpus.graph,
        )

        return assistant.lookup(cleaned_query)
