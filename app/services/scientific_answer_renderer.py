from __future__ import annotations

from app.services.scientific_answer_builder import (
    StructuredScientificAnswer,
)


class ScientificAnswerRenderer:
    """
    Produit une formulation textuelle deterministe
    a partir d'une reponse scientifique structuree.

    Le renderer ne deduit aucun fait scientifique.
    Il formule uniquement les informations deja
    presentes dans StructuredScientificAnswer.
    """

    def render(
        self,
        answer: StructuredScientificAnswer,
    ) -> str:
        if not isinstance(
            answer,
            StructuredScientificAnswer,
        ):
            raise TypeError(
                "answer doit etre un "
                "StructuredScientificAnswer."
            )

        if (
            not answer.found
            or not answer.document_results
        ):
            return (
                "Aucun document ne correspond "
                "a la recherche."
            )

        document_count = len(
            answer.document_results
        )

        if document_count == 1:
            introduction = (
                "1 document correspond "
                "a la recherche."
            )
        else:
            introduction = (
                f"{document_count} documents "
                "correspondent a la recherche."
            )

        parts = [introduction]

        for document_result in (
            answer.document_results
        ):
            studied_labels = [
                concept.label
                for concept
                in document_result.studied_concepts
            ]

            method_labels = [
                method.label
                for method
                in document_result.methods
            ]

            if studied_labels:
                if len(studied_labels) == 1:
                    parts.append(
                        f"{studied_labels[0]} "
                        "est etudie."
                    )
                else:
                    parts.append(
                        "Concepts etudies : "
                        + ", ".join(studied_labels)
                        + "."
                    )

            if method_labels:
                if len(method_labels) == 1:
                    parts.append(
                        "Methode utilisee : "
                        f"{method_labels[0]}."
                    )
                else:
                    parts.append(
                        "Methodes utilisees : "
                        + ", ".join(method_labels)
                        + "."
                    )

        return " ".join(parts)
