from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_search_page_displays_form() -> None:
    response = client.get("/search/")

    assert response.status_code == 200
    assert 'name="query"' in response.text
    assert "<form" in response.text


def test_search_navigation_is_enabled() -> None:
    response = client.get("/search/")

    assert response.status_code == 200
    assert 'href="/search/"' in response.text
    assert 'class="nav-link active"' in response.text


def test_search_page_displays_matching_document(
    tmp_path,
    monkeypatch,
) -> None:
    from types import SimpleNamespace

    import app.routers.search as search_router

    (tmp_path / "wine.md").write_text(
        "# Wine study\n\nLe vin est analyse.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        search_router,
        "get_settings",
        lambda: SimpleNamespace(nrip_root=tmp_path),
        raising=False,
    )

    response = client.get("/search/?query=vin")

    assert response.status_code == 200
    assert "Wine study" in response.text
    assert "vin" in response.text.lower()


def test_search_page_displays_no_results(
    tmp_path,
    monkeypatch,
) -> None:
    from types import SimpleNamespace

    import app.routers.search as search_router

    (tmp_path / "wine.md").write_text(
        "# Wine study\n\nLe vin est analyse.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        search_router,
        "get_settings",
        lambda: SimpleNamespace(nrip_root=tmp_path),
        raising=False,
    )

    response = client.get(
        "/search/?query=concept-inexistant-xyz"
    )

    assert response.status_code == 200
    assert "Aucun document" in response.text
    assert "Wine study" not in response.text


def test_search_page_without_query_does_not_load_corpus(
    monkeypatch,
) -> None:
    import app.services.scientific_search_service as search_service

    def unexpected_load(*args, **kwargs):
        raise AssertionError(
            "Le corpus ne doit pas etre charge sans requete."
        )

    monkeypatch.setattr(
        search_service.ScientificCorpusService,
        "load",
        unexpected_load,
    )

    response = client.get("/search/")

    assert response.status_code == 200
    assert 'name="query"' in response.text


def test_search_page_ignores_blank_query(
    monkeypatch,
) -> None:
    import app.services.scientific_search_service as search_service

    def unexpected_load(*args, **kwargs):
        raise AssertionError(
            "Blank query must not load the corpus."
        )

    monkeypatch.setattr(
        search_service.ScientificCorpusService,
        "load",
        unexpected_load,
    )

    response = client.get(
        "/search/",
        params={"query": "   "},
    )

    assert response.status_code == 200
    assert 'name="query"' in response.text
    assert "Aucun document" not in response.text


def test_search_page_escapes_html_query(
    tmp_path,
    monkeypatch,
) -> None:
    from types import SimpleNamespace

    import app.routers.search as search_router

    (tmp_path / "wine.md").write_text(
        "# Wine study\n\nLe vin est analyse.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        search_router,
        "get_settings",
        lambda: SimpleNamespace(nrip_root=tmp_path),
    )

    response = client.get(
        "/search/",
        params={"query": "<script>alert(1)</script>"},
    )

    assert response.status_code == 200
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;" in response.text


def test_search_page_displays_document_relative_path(
    tmp_path,
    monkeypatch,
) -> None:
    from types import SimpleNamespace

    import app.routers.search as search_router

    nested = tmp_path / "research"
    nested.mkdir()

    (nested / "wine.md").write_text(
        "# Wine provenance study\n\nLe vin est analyse.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        search_router,
        "get_settings",
        lambda: SimpleNamespace(nrip_root=tmp_path),
    )

    response = client.get(
        "/search/",
        params={"query": "vin"},
    )

    assert response.status_code == 200
    assert "Wine provenance study" in response.text
    assert "research/wine.md" in response.text.replace(
        "\\", "/"
    )


def test_search_page_identifies_unknown_concept(
    tmp_path,
    monkeypatch,
) -> None:
    from types import SimpleNamespace

    import app.routers.search as search_router

    (tmp_path / "wine.md").write_text(
        "# Wine study\n\nLe vin est analyse.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        search_router,
        "get_settings",
        lambda: SimpleNamespace(nrip_root=tmp_path),
    )

    response = client.get(
        "/search/",
        params={"query": "concept-inexistant-xyz"},
    )

    assert response.status_code == 200
    assert "Concept non reconnu" in response.text


def test_search_page_displays_recognized_concept_identity(
    tmp_path,
    monkeypatch,
) -> None:
    from types import SimpleNamespace

    import app.routers.search as search_router

    (tmp_path / "wine.md").write_text(
        "# Wine study\n\nLe vin est analyse.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        search_router,
        "get_settings",
        lambda: SimpleNamespace(nrip_root=tmp_path),
    )

    response = client.get(
        "/search/",
        params={"query": "vin"},
    )

    assert response.status_code == 200
    assert "Concept reconnu" in response.text
    assert "Identifiant du concept" in response.text
    assert "Wine study" in response.text


def test_search_page_displays_occurrence_evidence(
    tmp_path,
    monkeypatch,
) -> None:
    from types import SimpleNamespace

    import app.routers.search as search_router

    (tmp_path / "research").mkdir()

    (tmp_path / "research" / "wine.md").write_text(
        "# Wine study\n\nLe vin est analyse.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        search_router,
        "get_settings",
        lambda: SimpleNamespace(nrip_root=tmp_path),
    )

    response = client.get(
        "/search/",
        params={"query": "vin"},
    )

    assert response.status_code == 200
    assert "Preuves d'occurrence" in response.text
    assert "research/wine.md" in response.text.replace(
        "\\", "/"
    )
    assert "Le vin est analyse." in response.text


def test_search_page_identifies_taxonomy_concept_without_graph_node(
    tmp_path,
    monkeypatch,
) -> None:
    from types import SimpleNamespace

    import app.routers.search as search_router

    from app.services.assistant_engine import AssistantResult
    from app.services.scientific_search_service import (
        ScientificSearchService,
    )

    monkeypatch.setattr(
        search_router,
        "get_settings",
        lambda: SimpleNamespace(nrip_root=tmp_path),
    )

    def fake_search(self, root, query):
        return AssistantResult(
            query=query,
            found=False,
            concept_id=(
                "concept:organism.microorganism.yeast.brettanomyces"
            ),
            concept_label="Brettanomyces",
        )

    monkeypatch.setattr(
        ScientificSearchService,
        "search",
        fake_search,
    )

    response = client.get(
        "/search/",
        params={"query": "Brettanomyces"},
    )

    assert response.status_code == 200

    assert (
        "Concept identifié dans la taxonomie"
        in response.text
    )

    assert "Brettanomyces" in response.text

    assert (
        "concept:organism.microorganism.yeast.brettanomyces"
        in response.text
    )

    assert "Concept non reconnu" not in response.text



def test_search_page_collapses_long_occurrence_evidence(
    tmp_path,
    monkeypatch,
) -> None:
    from types import SimpleNamespace

    import app.routers.search as search_router

    from app.services.assistant_engine import (
        AssistantResult,
        AssistantEvidence,
    )
    from app.services.scientific_search_service import (
        ScientificSearchService,
    )

    from app.models.knowledge_graph import GraphNode
    from app.models.detected_entity import DetectedEntity

    monkeypatch.setattr(
        search_router,
        "get_settings",
        lambda: SimpleNamespace(nrip_root=tmp_path),
    )

    source_text = (
        "START_SOURCE_MARKER "
        + ("Scientific evidence content. " * 30)
        + " END_SOURCE_MARKER"
    )

    document = GraphNode(
        node_id="document:test",
        node_type="document",
        label="Test document",
        metadata={"relative_path": "research/test.md"},
    )

    concept = GraphNode(
        node_id="concept:wine",
        node_type="concept",
        label="Vin",
    )

    occurrence = DetectedEntity(
        value="vin",
        canonical="wine",
        category="domain",
        confidence=1.0,
        taxonomy_id="wine",
        start=0,
        end=3,
        source_text=source_text,
    )

    result = AssistantResult(
        query="vin",
        found=True,
        concept_id="concept:wine",
        concept_label="Vin",
        documents=[document],
        evidence=[
            AssistantEvidence(
                document=document,
                concept=concept,
                occurrence=occurrence,
            )
        ],
    )

    monkeypatch.setattr(
        ScientificSearchService,
        "search",
        lambda self, root, query: result,
    )

    response = client.get(
        "/search/",
        params={"query": "vin"},
    )

    assert response.status_code == 200

    assert "<details" in response.text
    assert "<summary>" in response.text
    assert "Consulter le texte source integral" in response.text

    from html import unescape

    html = unescape(response.text)

    assert "START_SOURCE_MARKER" in html
    assert "END_SOURCE_MARKER" in html

    preview = source_text[:300] + "..."

    assert preview in html
    assert source_text in html
    assert html.count("<details>") == 1
    assert html.count("</details>") == 1



def test_search_page_keeps_short_occurrence_visible(
    tmp_path,
    monkeypatch,
) -> None:
    from types import SimpleNamespace

    import app.routers.search as search_router

    from app.models.knowledge_graph import GraphNode
    from app.models.detected_entity import DetectedEntity
    from app.services.assistant_engine import (
        AssistantResult,
        AssistantEvidence,
    )
    from app.services.scientific_search_service import (
        ScientificSearchService,
    )

    monkeypatch.setattr(
        search_router,
        "get_settings",
        lambda: SimpleNamespace(nrip_root=tmp_path),
    )

    source_text = "Short scientific source: vin."

    document = GraphNode(
        node_id="document:short",
        node_type="document",
        label="Short document",
        metadata={"relative_path": "research/short.md"},
    )

    concept = GraphNode(
        node_id="concept:wine",
        node_type="concept",
        label="Vin",
    )

    occurrence = DetectedEntity(
        value="vin",
        canonical="wine",
        category="domain",
        taxonomy_id="wine",
        source_text=source_text,
    )

    result = AssistantResult(
        query="vin",
        found=True,
        concept_id="concept:wine",
        concept_label="Vin",
        documents=[document],
        evidence=[
            AssistantEvidence(
                document=document,
                concept=concept,
                occurrence=occurrence,
            )
        ],
    )

    monkeypatch.setattr(
        ScientificSearchService,
        "search",
        lambda self, root, query: result,
    )

    response = client.get(
        "/search/",
        params={"query": "vin"},
    )

    assert response.status_code == 200
    assert source_text in response.text
    assert "<details" not in response.text
    assert "Consulter le texte source integral" not in response.text
