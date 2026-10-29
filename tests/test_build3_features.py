"""Build 3: curated company sets for every canonical company, company-request endpoint,
requirements pin guard. No paid provider requests."""
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import accounts, companies, company_sets
from app.main import app

client = TestClient(app)


def _clear_limits():
    from app.main import _company_req_limiter
    _company_req_limiter.hits.clear()


def test_every_canonical_company_has_a_curated_set():
    names = companies.names()
    assert len(names) >= 30
    for n in names:
        cs = company_sets.for_company(n)
        assert cs is not None, f"no curated set for {n}"
        assert cs["curated"] is True
        qs = cs["questions"]
        assert len(qs) == 7, f"{n}: expected 7 questions, got {len(qs)}"
        types = {q["type"] for q in qs}
        assert "behavioral" in types and "technical" in types, f"{n}: missing core types"
        for q in qs:
            assert q["type"] in ("behavioral", "technical", "scenario")
            assert q["level"] in ("easy", "medium", "hard")
            assert 10 <= len(q["question"]) <= 400
            assert 10 <= len(q["hint"]) <= 400


def test_company_sets_disclaimer_present():
    for n in companies.names():
        note = company_sets.for_company(n)["note"]
        assert "written by MockRep" in note
        assert "Not leaked questions" in note


def test_company_request_stored_and_validated():
    _clear_limits()
    r = client.post("/api/company-request", json={"company": "Flipkart"})
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    with accounts.Conn() as c:
        rows = c.run("SELECT company FROM company_requests")
    assert rows[-1]["company"] == "Flipkart"
    # too short -> 400 from the helper
    r = client.post("/api/company-request", json={"company": "x"})
    assert r.status_code == 400
    # oversized -> 422 from the schema
    assert client.post("/api/company-request", json={"company": "y" * 200}).status_code == 422


def test_company_request_honeypot_stores_nothing():
    _clear_limits()
    with accounts.Conn() as c:
        before = c.run("SELECT COUNT(*) AS n FROM company_requests")[0]["n"]
    r = client.post("/api/company-request", json={"company": "EvilCorp", "website": "http://spam"})
    assert r.status_code == 200
    assert r.json()["ok"] is True  # pretend success
    with accounts.Conn() as c:
        after = c.run("SELECT COUNT(*) AS n FROM company_requests")[0]["n"]
    assert after == before  # but store nothing


def test_company_request_rate_limited():
    _clear_limits()
    for _ in range(10):
        assert client.post("/api/company-request", json={"company": "SomeCo"}).status_code == 200
    assert client.post("/api/company-request", json={"company": "SomeCo"}).status_code == 429
    _clear_limits()


def test_requirements_all_pinned_no_urls():
    """Every dependency is version-pinned (== or bounded range); no VCS/URL installs that
    bypass review and could silently change the deployed build."""
    req = Path(__file__).resolve().parent.parent / "requirements.txt"
    for line in req.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        assert not re.search(r"@\s*(git\+|https?://)", line), f"URL install: {line}"
        name = re.split(r"[<>=!\[]", line)[0].strip().lower()
        if name == "certifi":
            continue  # lower-bound-only by design; covered by the next test
        assert ("==" in line) or (">=" in line and "<" in line), f"unbounded requirement: {line}"
        assert "*" not in line.split("==")[0], f"wildcard: {line}"


def test_requirements_no_unbounded_lower_bound():
    """certifi is intentionally lower-bound-only for CA freshness; everything else must be
    exactly pinned (==) or carry an upper bound so a bad major release cannot auto-deploy."""
    req = Path(__file__).resolve().parent.parent / "requirements.txt"
    allow_lower_only = {"certifi"}
    for line in req.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = re.split(r"[<>=!\[]", line)[0].strip().lower()
        if name in allow_lower_only:
            continue
        if "==" in line:
            continue
        assert "<" in line, f"{name}: range without upper bound"
