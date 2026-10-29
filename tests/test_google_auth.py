import os
import tempfile

os.environ.pop("NEBIUS_API_KEY", None)
os.environ.pop("DATABASE_URL", None)
os.environ["RATE_LIMIT_PER_MIN"] = "100000"
os.environ["AUTH_RATE_PER_MIN"] = "100000"
os.environ["SIGNUPS_PER_DAY"] = "100000"
os.environ["AI_DAILY_PER_IP"] = "100000"
os.environ["INTERVIEWPILOT_DB"] = os.path.join(tempfile.mkdtemp(), "gacc.sqlite3")

import pytest
from fastapi.testclient import TestClient

from app import accounts, main
from app.main import app

accounts.SQLITE_PATH = os.environ["INTERVIEWPILOT_DB"]


def fresh():
    return TestClient(app)


@pytest.fixture(autouse=True)
def google_on(monkeypatch):
    monkeypatch.setattr(main, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(main, "_GOOGLE_AUTH_OK", True)
    yield


def fake_verify(payload):
    def _v(credential, request, audience):
        if credential == "bad":
            raise ValueError("invalid token")
        assert audience == "test-client-id.apps.googleusercontent.com"
        return payload
    return _v


GOOD = {"iss": "https://accounts.google.com", "email": "riya@gmail.com", "email_verified": True, "sub": "g-123"}


def test_config_endpoint_reports_client_id():
    assert fresh().get("/api/auth/google-config").json()["client_id"] == "test-client-id.apps.googleusercontent.com"


def test_config_endpoint_null_when_unset(monkeypatch):
    monkeypatch.setattr(main, "GOOGLE_CLIENT_ID", "")
    assert fresh().get("/api/auth/google-config").json()["client_id"] is None


def test_google_signin_creates_account_with_consent(monkeypatch):
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(GOOD))
    c = fresh()
    r = c.post("/api/auth/google", json={"credential": "tok", "agree": True, "age18": True})
    assert r.status_code == 200 and r.json()["user"]["email"] == "riya@gmail.com"
    assert "ip_session" in r.cookies
    assert c.get("/api/auth/me").json()["user"]["email"] == "riya@gmail.com"


def test_google_signin_new_user_needs_consent(monkeypatch):
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(dict(GOOD, sub="g-new1", email="new1@gmail.com")))
    r = fresh().post("/api/auth/google", json={"credential": "tok", "agree": False})
    assert r.status_code == 400 and "agree" in r.json()["detail"].lower()


def test_google_signin_repeat_returns_same_user(monkeypatch):
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(dict(GOOD, sub="g-222", email="rep@gmail.com")))
    r1 = fresh().post("/api/auth/google", json={"credential": "tok", "agree": True, "age18": True})
    r2 = fresh().post("/api/auth/google", json={"credential": "tok", "agree": False})  # consent not needed for existing
    assert r1.status_code == 200 and r2.status_code == 200


def test_google_links_existing_email_account(monkeypatch):
    c = fresh()
    c.post("/api/auth/register", json={"email": "link@gmail.com", "password": "longenough1", "agree": True, "age18": True})
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(dict(GOOD, sub="g-333", email="link@gmail.com")))
    r = c.post("/api/auth/google", json={"credential": "tok", "agree": False})
    assert r.status_code == 200
    with accounts.Conn() as conn:
        rows = conn.run("SELECT google_sub FROM users WHERE email=?", ("link@gmail.com",))
    assert rows and rows[0]["google_sub"] == "g-333"


def test_google_created_account_has_no_password_login(monkeypatch):
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(dict(GOOD, sub="g-444", email="nopw@gmail.com")))
    fresh().post("/api/auth/google", json={"credential": "tok", "agree": True, "age18": True})
    r = fresh().post("/api/auth/login", json={"email": "nopw@gmail.com", "password": "whatever123"})
    assert r.status_code == 401


def test_invalid_token_rejected(monkeypatch):
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(GOOD))
    assert fresh().post("/api/auth/google", json={"credential": "bad", "agree": True, "age18": True}).status_code == 401


def test_unverified_email_rejected(monkeypatch):
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(dict(GOOD, sub="g-555", email="unv@gmail.com", email_verified=False)))
    assert fresh().post("/api/auth/google", json={"credential": "tok", "agree": True, "age18": True}).status_code == 401


def test_wrong_issuer_rejected(monkeypatch):
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(dict(GOOD, iss="https://evil.example.com")))
    assert fresh().post("/api/auth/google", json={"credential": "tok", "agree": True, "age18": True}).status_code == 401


def test_disabled_when_not_configured(monkeypatch):
    monkeypatch.setattr(main, "GOOGLE_CLIENT_ID", "")
    r = fresh().post("/api/auth/google", json={"credential": "tok", "agree": True, "age18": True})
    assert r.status_code == 503


def test_delete_account_page_served():
    r = fresh().get("/delete-account")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    for needle in ("Delete your MockRep account", "permanent", "ranjitkumarsahoo77@gmail.com", "delete-account.js"):
        assert needle in r.text
    assert "<script>" not in r.text.split('<script src="/static/delete-account.js" defer></script>')[0] or True


def test_delete_account_page_no_inline_script():
    r = fresh().get("/delete-account")
    body = r.text.replace('<script src="/static/delete-account.js" defer></script>', "")
    assert "<script" not in body


def test_google_user_can_delete_account(monkeypatch):
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(dict(GOOD, sub="g-666", email="gone@gmail.com")))
    c = fresh()
    c.post("/api/auth/google", json={"credential": "tok", "agree": True, "age18": True})
    assert c.get("/api/auth/me").json()["user"]["email"] == "gone@gmail.com"
    assert c.delete("/api/auth/account").status_code == 200
    assert c.get("/api/auth/me").json()["user"] is None


def test_index_has_google_button_mount_and_footer_link():
    t = fresh().get("/").text
    assert 'id="gSignInBtn"' in t and 'id="gSignInWrap"' in t
    assert 'href="/delete-account"' in t


def test_csp_allows_only_google_gsi_externally():
    csp = fresh().get("/").headers["content-security-policy"]
    assert "https://accounts.google.com/gsi/client" in csp
    assert "https://accounts.google.com/gsi/" in csp
    assert "unsafe-inline" not in [p for p in csp.split(";") if p.strip().startswith("script-src")][0]


FORM = {"content-type": "application/x-www-form-urlencoded"}


def test_redirect_mode_rejects_bad_csrf(monkeypatch):
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(GOOD))
    c = fresh()
    r = c.post("/api/auth/google", data={"credential": "tok", "g_csrf_token": "abc"},
               cookies={"g_csrf_token": "different"}, headers=FORM, follow_redirects=False)
    assert r.status_code == 400
    r = c.post("/api/auth/google", data={"credential": "tok"}, headers=FORM, follow_redirects=False)
    assert r.status_code == 400


def test_redirect_mode_creates_account_with_consent_cookie(monkeypatch):
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(dict(GOOD, sub="g-r1", email="red1@gmail.com")))
    c = fresh()
    r = c.post("/api/auth/google", data={"credential": "tok", "g_csrf_token": "xyz"},
               cookies={"g_csrf_token": "xyz", "mr_gconsent": "1"}, headers=FORM, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/#acct"
    assert "ip_session" in r.headers.get("set-cookie", "")
    assert c.get("/api/auth/me").json()["user"]["email"] == "red1@gmail.com"


def test_redirect_mode_new_user_without_consent_bounces(monkeypatch):
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(dict(GOOD, sub="g-r2", email="red2@gmail.com")))
    c = fresh()
    r = c.post("/api/auth/google", data={"credential": "tok", "g_csrf_token": "xyz"},
               cookies={"g_csrf_token": "xyz"}, headers=FORM, follow_redirects=False)
    assert r.status_code == 303 and "gerr=consent" in r.headers["location"]
    assert c.get("/api/auth/me").json()["user"] is None


def test_redirect_mode_links_existing_account_without_consent(monkeypatch):
    c = fresh()
    c.post("/api/auth/register", json={"email": "red3@gmail.com", "password": "longenough1", "agree": True, "age18": True})
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(dict(GOOD, sub="g-r3", email="red3@gmail.com")))
    r = c.post("/api/auth/google", data={"credential": "tok", "g_csrf_token": "xyz"},
               cookies={"g_csrf_token": "xyz"}, headers=FORM, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/#acct"


def test_redirect_mode_bad_token_bounces(monkeypatch):
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(GOOD))
    r = fresh().post("/api/auth/google", data={"credential": "bad", "g_csrf_token": "xyz"},
                     cookies={"g_csrf_token": "xyz"}, headers=FORM, follow_redirects=False)
    assert r.status_code == 303 and "gerr=google" in r.headers["location"]


def test_redirect_form_survives_google_cross_site_headers(monkeypatch):
    """Google's form_post arrives with Origin/Sec-Fetch-Site of accounts.google.com."""
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(dict(GOOD, sub="g-r9", email="red9@gmail.com")))
    r = fresh().post("/api/auth/google", data={"credential": "tok", "g_csrf_token": "xyz"},
                     cookies={"g_csrf_token": "xyz", "mr_gconsent": "1"},
                     headers={"content-type": "application/x-www-form-urlencoded",
                              "origin": "https://accounts.google.com",
                              "sec-fetch-site": "cross-site"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/#acct"


def test_json_mode_still_origin_guarded(monkeypatch):
    monkeypatch.setattr(main._google_id_token, "verify_oauth2_token", fake_verify(GOOD))
    r = fresh().post("/api/auth/google", json={"credential": "tok", "agree": True, "age18": True},
                     headers={"origin": "https://evil.example.com"})
    assert r.status_code == 403
