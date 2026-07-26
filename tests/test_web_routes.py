from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dashboard_is_available() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "NRIP Admin" in response.text
    assert "Tableau de bord" in response.text


def test_document_catalog_is_available() -> None:
    response = client.get("/documents/", follow_redirects=True)

    assert response.status_code == 200
    assert "Catalogue documentaire" in response.text


def test_summary_api_is_available() -> None:
    response = client.get("/api/catalog/summary")

    assert response.status_code == 200
    assert "document_count" in response.json()

def test_stylesheet_is_available() -> None:
    response = client.get("/static/css/app.css")

    assert response.status_code == 200
    assert ":root" in response.text
    assert "text/css" in response.headers["content-type"]