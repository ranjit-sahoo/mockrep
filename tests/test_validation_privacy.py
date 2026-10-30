"""Regression tests for the 2026-10-30 review fixes:
1. 422 validation responses must never reflect submitted values (a too-long
   password was previously echoed back by FastAPI's default handler).
2. The uvicorn access-log filter must mask guest-session bearer IDs in URL paths.
"""
import logging

from fastapi.testclient import TestClient

from app.main import _AccessLogSidFilter, app


def test_422_does_not_reflect_password_value():
    client = TestClient(app)
    secret = "x" * 300
    r = client.post(
        "/api/auth/register",
        json={"email": "a@b.co", "password": secret, "agree": True, "age18": True, "website": "", "role": "candidate"},
    )
    assert r.status_code == 422
    body = r.text
    assert secret not in body
    for err in r.json()["detail"]:
        assert "input" not in err


def test_422_still_reports_field_and_reason():
    client = TestClient(app)
    r = client.post("/api/session", json={"resume": 123, "role": 999})
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert any("resume" in e.get("loc", []) for e in detail)
    assert all(e.get("msg") for e in detail)


def test_access_log_filter_masks_session_id():
    f = _AccessLogSidFilter()
    sid = "a" * 24
    rec = logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1, '"GET /api/session/%s/state HTTP/1.1" 200', (sid,), None)
    f.filter(rec)
    out = rec.getMessage()
    assert sid not in out
    assert "/api/session/***/state" in out


def test_access_log_filter_leaves_other_paths():
    f = _AccessLogSidFilter()
    rec = logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1, '"POST /api/session HTTP/1.1" 200', (), None)
    f.filter(rec)
    assert "POST /api/session " in rec.getMessage()
