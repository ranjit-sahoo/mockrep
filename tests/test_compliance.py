"""Compliance audit regressions: full account-data wipe on deletion, share-card
report + moderation takedown (Play UGC policy), and policy pages covering the
features that actually store data."""
import os
import tempfile

os.environ.pop("NEBIUS_API_KEY", None)
os.environ.pop("DATABASE_URL", None)
os.environ["RATE_LIMIT_PER_MIN"] = "100000"
os.environ["AUTH_RATE_PER_MIN"] = "100000"
os.environ["SIGNUPS_PER_DAY"] = "100000"
os.environ["AI_DAILY_PER_IP"] = "100000"
os.environ["COMPANY_REQUESTS_PER_DAY"] = "100000"
os.environ["INTERVIEWPILOT_DB"] = os.path.join(tempfile.mkdtemp(), "comp.sqlite3")

from fastapi.testclient import TestClient

from app import accounts, card
from app.main import app

accounts.SQLITE_PATH = os.environ["INTERVIEWPILOT_DB"]
c = TestClient(app)

EMAIL = "wipe@example.com"
PW = "longenough1"


def _uid():
    with accounts.Conn() as conn:
        rows = conn.run("SELECT id FROM users WHERE email=?", (EMAIL,))
    return rows[0]["id"]


def test_delete_account_wipes_waitlist_company_requests_and_recovery():
    r = c.post("/api/auth/register", json={"email": EMAIL, "password": PW, "agree": True, "age18": True})
    assert r.status_code == 200, r.text
    uid = _uid()
    # join waitlist, file a company request, create a recovery code
    c.post("/api/waitlist", json={"email": EMAIL})
    c.post("/api/company-request", json={"company": "TestCorp"})
    accounts.recovery_create(uid)
    with accounts.Conn() as conn:
        assert conn.run("SELECT email FROM waitlist WHERE email=?", (EMAIL,))
        assert conn.run("SELECT id FROM company_requests WHERE email=?", (EMAIL,))
        assert conn.run("SELECT user_id FROM account_recovery WHERE user_id=?", (uid,))
    # delete the account
    r = c.delete("/api/auth/account")
    assert r.status_code == 200, r.text
    with accounts.Conn() as conn:
        assert not conn.run("SELECT id FROM users WHERE email=?", (EMAIL,))
        assert not conn.run("SELECT email FROM waitlist WHERE email=?", (EMAIL,))
        assert not conn.run("SELECT id FROM company_requests WHERE email=?", (EMAIL,))
        assert not conn.run("SELECT user_id FROM account_recovery WHERE user_id=?", (uid,))


def test_card_blocklist_hides_card_and_admin_endpoint_is_gated():
    payload = {"s": 4.0, "r": "Sales", "v": "Interview-ready", "l": "mid", "c": "IN", "st": [], "sk": [], "n": "Test", "d": "2026-10-30"}
    token = card.sign(payload)
    assert c.get(f"/c/{token}").status_code == 200
    assert c.get(f"/c/{token}.png").status_code == 200
    # admin endpoint: hidden without env token
    os.environ.pop("ADMIN_TOKEN", None)
    assert c.post("/api/admin/block-card", json={"token": token}).status_code == 404
    # with env token set: wrong header still 404
    os.environ["ADMIN_TOKEN"] = "secret-admin"
    assert c.post("/api/admin/block-card", json={"token": token}).status_code == 404
    # correct token blocks the card
    r = c.post("/api/admin/block-card", json={"token": token}, headers={"x-admin-token": "secret-admin"})
    assert r.status_code == 200, r.text
    assert c.get(f"/c/{token}").status_code == 404
    assert c.get(f"/c/{token}.png").status_code == 404
    os.environ.pop("ADMIN_TOKEN", None)


def test_card_page_has_report_link_and_external_js():
    payload = {"s": 3.0, "r": "Support", "v": "Getting there", "l": "mid", "c": "IN", "st": [], "sk": [], "n": "", "d": "2026-10-30"}
    token = card.sign(payload)
    r = c.get(f"/c/{token}")
    assert r.status_code == 200
    assert 'id="cardReport"' in r.text and "/static/card.js" in r.text
    assert "<script>" not in r.text  # CSP forbids inline scripts; report wiring must be external
    js = c.get("/static/card.js")
    assert js.status_code == 200 and "content-report" in js.text


def test_policy_pages_cover_current_data_use():
    priv = c.get("/privacy").text
    for needle in ("Grievance Officer", "never uploaded", "words per minute", "company name you typed",
                   "daily-practice streak", "October 30, 2026"):
        assert needle in priv, needle
    cook = c.get("/cookies").text
    assert "offline question pack" in cook and "streak" in cook
    terms = c.get("/terms").text
    assert "Share cards" in terms and "reported or unlawful cards" in terms
    dele = c.get("/delete-account").text
    assert "waitlist" in dele and "company requests" in dele
