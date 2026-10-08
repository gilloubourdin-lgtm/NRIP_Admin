from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.routers.documents as documents_router
from app.main import app


client = TestClient(app)


@pytest.fixture
def corpus_root(tmp_path, monkeypatch):
    root = tmp_path / "corpus"
    root.mkdir()

    monkeypatch.setattr(
        documents_router,
        "get_settings",
        lambda: SimpleNamespace(nrip_root=root),
    )

    return root


def test_document_view_displays_exact_source(corpus_root):
    folder = corpus_root / "research"
    folder.mkdir()

    (folder / "study.md").write_text(
        "# Scientific study\n\nEvidence for vin.\n",
        encoding="utf-8",
    )

    response = client.get(
        "/documents/view",
        params={"path": "research/study.md"},
    )

    assert response.status_code == 200
    assert "Scientific study" in response.text
    assert "Evidence for vin." in response.text
    assert "research/study.md" in response.text


def test_document_view_distinguishes_duplicate_ids(corpus_root):
    first = corpus_root / "a"
    second = corpus_root / "b"

    first.mkdir()
    second.mkdir()

    (first / "NRIP-001.md").write_text(
        "# First source\n\nFIRST_UNIQUE_MARKER\n",
        encoding="utf-8",
    )

    (second / "NRIP-001.md").write_text(
        "# Second source\n\nSECOND_UNIQUE_MARKER\n",
        encoding="utf-8",
    )

    response = client.get(
        "/documents/view",
        params={"path": "b/NRIP-001.md"},
    )

    assert response.status_code == 200
    assert "SECOND_UNIQUE_MARKER" in response.text
    assert "FIRST_UNIQUE_MARKER" not in response.text


def test_document_view_escapes_source_html(corpus_root):
    (corpus_root / "unsafe.md").write_text(
        "# Safety\n\n<script>alert(1)</script>\n",
        encoding="utf-8",
    )

    response = client.get(
        "/documents/view",
        params={"path": "unsafe.md"},
    )

    assert response.status_code == 200
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;" in response.text


@pytest.mark.parametrize(
    "path",
    [
        "../outside.md",
        "../../outside.md",
        "/etc/passwd",
        "C:/Windows/win.ini",
        r"C:\Windows\win.ini",
        "",
    ],
)
def test_document_view_rejects_unsafe_paths(
    corpus_root,
    path,
):
    response = client.get(
        "/documents/view",
        params={"path": path},
    )

    assert response.status_code in (400, 404, 422)


def test_document_view_rejects_missing_document(corpus_root):
    response = client.get(
        "/documents/view",
        params={"path": "missing.md"},
    )

    assert response.status_code == 404


def test_document_view_rejects_non_markdown(corpus_root):
    (corpus_root / "secret.txt").write_text(
        "PRIVATE_MARKER",
        encoding="utf-8",
    )

    response = client.get(
        "/documents/view",
        params={"path": "secret.txt"},
    )

    assert response.status_code in (400, 404)
    assert "PRIVATE_MARKER" not in response.text


def test_document_view_rejects_symlink_escape(
    corpus_root,
    tmp_path,
):
    outside = tmp_path / "outside.md"
    outside.write_text(
        "# Outside\n\nOUTSIDE_SECRET_MARKER\n",
        encoding="utf-8",
    )

    link = corpus_root / "linked.md"

    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip(
            "Symlink creation unavailable on this system."
        )

    response = client.get(
        "/documents/view",
        params={"path": "linked.md"},
    )

    assert response.status_code in (400, 404)
    assert "OUTSIDE_SECRET_MARKER" not in response.text


def test_catalog_links_to_document_source(corpus_root):
    from html import unescape

    folder = corpus_root / "research"
    folder.mkdir()

    (folder / "study.md").write_text(
        "# Catalog navigation\n\nSource content.\n",
        encoding="utf-8",
    )

    response = client.get("/documents/")

    assert response.status_code == 200

    html = unescape(response.text)

    assert "Catalog navigation" in html
    assert (
        'href="/documents/view?path=research%2Fstudy.md"'
        in html
    )


def test_search_links_to_exact_document_source(
    corpus_root,
    monkeypatch,
):
    from html import unescape

    import app.routers.search as search_router

    monkeypatch.setattr(
        search_router,
        "get_settings",
        lambda: SimpleNamespace(nrip_root=corpus_root),
    )

    folder = corpus_root / "research"
    folder.mkdir()

    (folder / "wine study.md").write_text(
        "# Wine navigation\n\nLe vin est analyse.\n",
        encoding="utf-8",
    )

    response = client.get(
        "/search/",
        params={"query": "vin"},
    )

    assert response.status_code == 200

    html = unescape(response.text)

    assert "Wine navigation" in html
    assert (
        'href="/documents/view?path=research%2Fwine%20study.md"'
        in html
    )
