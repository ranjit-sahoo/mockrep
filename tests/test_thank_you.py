"""Thank-you page and branded 404 contract. No paid provider requests."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_thank_you_page_branded():
    r = client.get("/thank-you")
    assert r.status_code == 200
    assert "You are on the list" in r.text
    assert 'content="noindex"' in r.text
    assert "MockRep" in r.text


def test_404_branded_for_browsers_json_for_api():
    r = client.get("/no-such-page", headers={"accept": "text/html,application/xhtml+xml"})
    assert r.status_code == 404
    assert "This page was not found" in r.text
    r2 = client.get("/no-such-page")
    assert r2.status_code == 404
    assert r2.json() == {"detail": "Not Found"}
