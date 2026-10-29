import os
import tempfile

os.environ.pop("NEBIUS_API_KEY", None)
os.environ.pop("DATABASE_URL", None)
os.environ["RATE_LIMIT_PER_MIN"] = "100000"
os.environ["AUTH_RATE_PER_MIN"] = "100000"
os.environ["SIGNUPS_PER_DAY"] = "100000"
os.environ["AI_DAILY_PER_IP"] = "100000"
os.environ["AI_DAILY_PER_USER"] = "100000"
os.environ["INTERVIEWPILOT_DB"] = os.path.join(tempfile.mkdtemp(), "bill.sqlite3")

from fastapi.testclient import TestClient

from app import accounts, billing
from app.main import app

accounts.SQLITE_PATH = os.environ["INTERVIEWPILOT_DB"]


def _mk(email="bill@example.com"):
    c = TestClient(app)
    assert c.post("/api/auth/register", json={"agree": True, "age18": True, "email": email, "password": "longenough1"}).status_code == 200
    return c


def test_billing_hidden_when_disabled():
    c = _mk()
    assert c.get("/api/billing/config").json() == {"enabled": False, "products": []}
    assert c.post("/api/billing/verify", json={"product_id": "x", "purchase_token": "y"}).status_code == 404
    assert c.get("/api/billing/status").status_code == 404


def test_verify_grants_premium_for_active_subscription():
    c = _mk("sub@example.com")
    old = (billing.ENABLED, billing._service_token, billing._play_get)
    billing.ENABLED = True
    billing._service_token = lambda: "fake-token"
    billing._play_get = lambda url, token: {
        "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
        "lineItems": [{"expiryTime": "2099-01-01T00:00:00Z"}],
    }
    try:
        r = c.post("/api/billing/verify", json={"product_id": "mockrep_premium_monthly", "purchase_token": "tok123"})
        assert r.status_code == 200, r.text
        ent = r.json()["entitlement"]
        assert ent["plan_id"] == "premium" and ent["state"] == "active" and ent["source"] == "play"
        me = c.get("/api/auth/me").json()
        assert me["user"]["plan"] == "premium"
        st = c.get("/api/billing/status").json()["entitlement"]
        assert st["plan_id"] == "premium"
    finally:
        billing.ENABLED, billing._service_token, billing._play_get = old


def test_inactive_subscription_and_unknown_product_rejected():
    c = _mk("inactive@example.com")
    old = (billing.ENABLED, billing._service_token, billing._play_get)
    billing.ENABLED = True
    billing._service_token = lambda: "fake-token"
    billing._play_get = lambda url, token: {"subscriptionState": "SUBSCRIPTION_STATE_CANCELED"}
    try:
        assert c.post("/api/billing/verify", json={"product_id": "nope", "purchase_token": "t"}).status_code == 400
        r = c.post("/api/billing/verify", json={"product_id": "mockrep_premium_monthly", "purchase_token": "t"})
        assert r.status_code == 403
        assert c.get("/api/auth/me").json()["user"]["plan"] == "free"
    finally:
        billing.ENABLED, billing._service_token, billing._play_get = old


def test_billing_verify_requires_login():
    old = billing.ENABLED
    billing.ENABLED = True
    try:
        assert TestClient(app).post("/api/billing/verify", json={"product_id": "mockrep_premium_monthly", "purchase_token": "t"}).status_code == 401
    finally:
        billing.ENABLED = old
