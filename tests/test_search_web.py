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
