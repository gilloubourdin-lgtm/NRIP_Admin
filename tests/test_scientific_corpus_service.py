from pathlib import Path

from app.services.scientific_corpus_service import (
    ScientificCorpusService,
)


def test_load_scientific_corpus_builds_graph(
    tmp_path: Path,
) -> None:
    source = tmp_path / "NRIP-TEST.md"

    source.write_text(
        "# Scientific corpus test\n\n"
        "Le vin contient des informations scientifiques.\n",
        encoding="utf-8",
    )

    service = ScientificCorpusService()

    result = service.load(tmp_path)

    assert len(result.documents) == 1

    document = result.documents[0]

    assert document.title == "Scientific corpus test"
    assert document.relative_path == "NRIP-TEST.md"

    assert result.graph is not None

    document_nodes = [
        node
        for node in result.graph.nodes.values()
        if node.node_type == "document"
    ]

    assert len(document_nodes) == 1


def test_empty_scientific_corpus(
    tmp_path: Path,
) -> None:
    result = ScientificCorpusService().load(tmp_path)

    assert result.documents == []
    assert len(result.graph.nodes) == 0
    assert len(result.graph.edges) == 0


def test_missing_scientific_corpus_directory(
    tmp_path: Path,
) -> None:
    import pytest

    missing = tmp_path / "missing"

    with pytest.raises(ValueError):
        ScientificCorpusService().load(missing)


def test_nested_scientific_documents(
    tmp_path: Path,
) -> None:
    nested = tmp_path / "research"
    nested.mkdir()

    (tmp_path / "root.md").write_text(
        "# Root document\n\nRoot content.\n",
        encoding="utf-8",
    )

    (nested / "nested.md").write_text(
        "# Nested document\n\nNested content.\n",
        encoding="utf-8",
    )

    result = ScientificCorpusService().load(tmp_path)

    assert len(result.documents) == 2

    paths = {
        document.relative_path
        for document in result.documents
    }

    assert paths == {
        "root.md",
        "research/nested.md",
    }

    document_nodes = [
        node
        for node in result.graph.nodes.values()
        if node.node_type == "document"
    ]

    assert len(document_nodes) == 2


def test_scientific_corpus_enriches_taxonomy(
    tmp_path: Path,
) -> None:
    (tmp_path / "wine.md").write_text(
        "# Wine study\n\nLe vin est analyse.\n",
        encoding="utf-8",
    )

    result = ScientificCorpusService().load(tmp_path)

    document = result.documents[0]

    assert any(
        entity.taxonomy_id == "wine"
        for entity in document.entities
    )

    assert "concept:wine" in result.graph.nodes


def test_corpus_handles_duplicate_document_ids(
    tmp_path,
) -> None:
    from app.services.scientific_corpus_service import (
        ScientificCorpusService,
    )

    first = tmp_path / "volume"
    second = tmp_path / "volume" / "part"
    first.mkdir()
    second.mkdir()

    (first / "NRIP-102_Foreword.md").write_text(
        "# Foreword\n\nLe vin est analyse.\n",
        encoding="utf-8",
    )

    (second / "NRIP-102_Copyright.md").write_text(
        "# Copyright\n\nLe vin est etudie.\n",
        encoding="utf-8",
    )

    corpus = ScientificCorpusService().load(tmp_path)

    assert len(corpus.documents) == 2

    document_nodes = [
        node
        for node in corpus.graph.nodes.values()
        if node.node_type == "document"
    ]

    assert len(document_nodes) == 2
    assert len({
        node.node_id
        for node in document_nodes
    }) == 2


def test_corpus_preserves_original_ids_after_disambiguation(
    tmp_path,
) -> None:
    from app.services.scientific_corpus_service import (
        ScientificCorpusService,
    )

    first = tmp_path / "volume"
    second = tmp_path / "volume" / "part"
    first.mkdir()
    second.mkdir()

    (first / "NRIP-102_Foreword.md").write_text(
        "# Foreword\n\nLe vin est analyse.\n",
        encoding="utf-8",
    )

    (second / "NRIP-102_Copyright.md").write_text(
        "# Copyright\n\nLe vin est etudie.\n",
        encoding="utf-8",
    )

    corpus = ScientificCorpusService().load(tmp_path)

    assert len(corpus.documents) == 2

    assert {
        document.document_id
        for document in corpus.documents
    } == {"NRIP-102"}

    document_nodes = [
        node
        for node in corpus.graph.nodes.values()
        if node.node_type == "document"
    ]

    assert {
        node.metadata["document_id"]
        for node in document_nodes
    } == {"NRIP-102"}

    assert {
        node.metadata["relative_path"]
        for node in document_nodes
    } == {
        "volume/NRIP-102_Foreword.md",
        "volume/part/NRIP-102_Copyright.md",
    }


def test_corpus_rejects_technical_id_collision(
    tmp_path,
) -> None:
    import pytest

    from app.services.scientific_corpus_service import (
        ScientificCorpusService,
    )

    first = tmp_path / "a"
    second = tmp_path / "b"

    first.mkdir()
    second.mkdir()

    (first / "NRIP-102_Foreword.md").write_text(
        "# Foreword\n",
        encoding="utf-8",
    )

    (second / "NRIP-102_Copyright.md").write_text(
        "# Copyright\n",
        encoding="utf-8",
    )

    (tmp_path / "special.md").write_text(
        "---\n"
        "document_id: NRIP-102@a/NRIP-102_Foreword.md\n"
        "---\n"
        "# Special document\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Collision d'identifiant technique",
    ):
        ScientificCorpusService().load(tmp_path)
