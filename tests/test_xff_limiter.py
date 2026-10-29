"""client_key must ignore spoofable leftmost X-Forwarded-For entries and key on the
last entry (the one Render's edge appends). Regression for the live-verified bypass:
rotating XFF used to rotate the rate-limit bucket."""
from starlette.testclient import TestClient
from app.guard import client_key
from app.main import app


def _req(xff):
    client = TestClient(app)
    req = client.build_request("GET", "/", headers={"x-forwarded-for": xff} if xff else {})
    return req


def test_leftmost_spoof_entries_ignored():
    assert client_key(_req("10.1.1.1, 10.2.2.2, 203.0.113.9")) == "203.0.113.9"


def test_single_honest_xff_used():
    assert client_key(_req("198.51.100.7")) == "198.51.100.7"


def test_rotating_spoofs_share_one_bucket():
    k1 = client_key(_req("10.9.9.1, 203.0.113.9"))
    k2 = client_key(_req("10.9.9.2, 203.0.113.9"))
    k3 = client_key(_req("8.8.8.8, 4.4.4.4, 203.0.113.9"))
    assert k1 == k2 == k3 == "203.0.113.9"


def test_no_xff_falls_back_to_peer():
    from starlette.requests import Request
    req = Request({"type": "http", "headers": [], "client": ("192.0.2.5", 1234), "server": ("t", 80), "scheme": "http", "method": "GET", "path": "/", "query_string": b""})
    assert client_key(req) == "192.0.2.5"
