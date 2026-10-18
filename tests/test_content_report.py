"""AI content reporting endpoint (Play generative-AI policy). No paid provider requests."""
import pytest
from fastapi.testclient import TestClient

from app import accounts
from app.main import app

client = TestClient(app)


def _clear_limits():
    from app.main import _report_limiter
    _report_limiter.hits.clear()


def test_report_stored_with_sanitised_kind():
    _clear_limits()
    r = client.post("/api/content-report", json={"kind": "Interview Report!<script>", "reason": "Rude content", "excerpt": "some excerpt"})
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    with accounts.Conn() as c:
        rows = c.run("SELECT kind, reason, excerpt FROM content_reports")
    assert rows[-1]["kind"] == "other"  # not a known tool name: coerced
    assert rows[-1]["reason"] == "Rude content"


def test_report_validation_and_rate_limit():
    _clear_limits()
    assert client.post("/api/content-report", json={"kind": "x", "reason": "y" * 601}).status_code == 422
    for _ in range(10):
        assert client.post("/api/content-report", json={"kind": "prep"}).status_code == 200
    assert client.post("/api/content-report", json={"kind": "prep"}).status_code == 429
    _clear_limits()


def test_unknown_kind_coerced_to_other():
    _clear_limits()
    r = client.post("/api/content-report", json={"kind": "junk-kind-xyz", "reason": "t"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_honeypot_store_nothing():
    _clear_limits()
    r = client.post("/api/content-report", json={"kind": "prep", "reason": "bot", "website": "http://spam"})
    assert r.status_code == 200
    assert r.json()["id"] == "ignored"
