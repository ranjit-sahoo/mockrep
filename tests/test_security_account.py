import os
import tempfile

os.environ.pop("NEBIUS_API_KEY", None)
os.environ.pop("DATABASE_URL", None)
os.environ["RATE_LIMIT_PER_MIN"] = "100000"
os.environ["AUTH_RATE_PER_MIN"] = "100000"
os.environ["SIGNUPS_PER_DAY"] = "100000"
os.environ["AI_DAILY_PER_IP"] = "100000"
os.environ["AI_DAILY_PER_USER"] = "100000"
os.environ["INTERVIEWPILOT_DB"] = os.path.join(tempfile.mkdtemp(), "secacc.sqlite3")

from fastapi.testclient import TestClient

from app import accounts
from app.main import app, _user_ai_limiter

accounts.SQLITE_PATH = os.environ["INTERVIEWPILOT_DB"]


def _mk(email):
    c = TestClient(app)
    r = c.post("/api/auth/register", json={"agree": True, "age18": True, "email": email, "password": "longenough1"})
    assert r.status_code == 200
    return c


def test_change_password_kills_other_sessions():
    a, b = _mk("pw@example.com"), TestClient(app)
    b.post("/api/auth/login", json={"email": "pw@example.com", "password": "longenough1"})
    assert b.get("/api/auth/me").json()["user"]
    # wrong current password is refused
    assert a.post("/api/auth/change-password", json={"current_password": "nope", "new_password": "newpassword9"}).status_code == 403
    assert a.post("/api/auth/change-password", json={"current_password": "longenough1", "new_password": "short"}).status_code == 400
    assert a.post("/api/auth/change-password", json={"current_password": "longenough1", "new_password": "newpassword9"}).status_code == 200
    # the changing session survives, every other session is dead
    assert a.get("/api/auth/me").json()["user"]["email"] == "pw@example.com"
    assert b.get("/api/auth/me").json()["user"] is None
    # old password no longer works, new one does
    assert TestClient(app).post("/api/auth/login", json={"email": "pw@example.com", "password": "longenough1"}).status_code == 401
    assert TestClient(app).post("/api/auth/login", json={"email": "pw@example.com", "password": "newpassword9"}).status_code == 200


def test_change_email_requires_password_and_uniqueness():
    a = _mk("mail@example.com")
    _mk("taken@example.com")
    assert a.post("/api/auth/change-email", json={"new_email": "x@example.com", "password": "wrong"}).status_code == 403
    assert a.post("/api/auth/change-email", json={"new_email": "taken@example.com", "password": "longenough1"}).status_code == 400
    assert a.post("/api/auth/change-email", json={"new_email": "not-an-email", "password": "longenough1"}).status_code == 400
    r = a.post("/api/auth/change-email", json={"new_email": "New@Example.com", "password": "longenough1"})
    assert r.status_code == 200 and r.json()["email"] == "new@example.com"
    assert a.get("/api/auth/me").json()["user"]["email"] == "new@example.com"
    # old email no longer logs in; new one does
    assert TestClient(app).post("/api/auth/login", json={"email": "mail@example.com", "password": "longenough1"}).status_code == 401
    assert TestClient(app).post("/api/auth/login", json={"email": "new@example.com", "password": "longenough1"}).status_code == 200


def test_account_export_contains_everything_and_requires_auth():
    assert TestClient(app).get("/api/account/export").status_code == 401
    c = _mk("exp@example.com")
    c.post("/api/history", json={"kind": "prep", "title": "T", "data": {"a": 1}})
    r = c.get("/api/account/export")
    assert r.status_code == 200
    assert "mockrep-my-data.json" in r.headers["content-disposition"]
    d = r.json()
    assert d["account"]["email"] == "exp@example.com"
    assert any(h["title"] == "T" and h["data"] == {"a": 1} for h in d["history"])
    assert "progress" in d and "speaking_progress" in d and "exported_at" in d


def test_per_user_ai_daily_cap_only_hits_signed_in_users():
    c = _mk("cap@example.com")
    with accounts.Conn() as conn:
        uid = conn.run("SELECT id FROM users WHERE email=?", ("cap@example.com",))[0]["id"]
    old = _user_ai_limiter.limit
    _user_ai_limiter.limit = 1
    try:
        _user_ai_limiter.hits.clear()
        assert _user_ai_limiter.check("u:" + uid) is True
        assert _user_ai_limiter.check("u:" + uid) is False
        r = c.post("/api/star", json={"question": "q", "answer": "a"})
        assert r.status_code == 429
        # a guest on the same IP is untouched by the per-user cap
        g = TestClient(app)
        assert g.post("/api/star", json={"question": "q", "answer": "a"}).status_code != 429
    finally:
        _user_ai_limiter.limit = old


def test_sql_injection_login_and_history():
    c = TestClient(app)
    assert c.post("/api/auth/login", json={"email": "' OR 1=1 --", "password": "x" * 8}).status_code == 401
    a = _mk("inj@example.com")
    evil = "'; DROP TABLE users;--"
    s = a.post("/api/history", json={"kind": "prep", "title": evil, "data": {}})
    assert s.status_code == 200
    assert a.get("/api/history").json()["items"][0]["title"] == evil
    assert TestClient(app).post("/api/auth/login", json={"email": "inj@example.com", "password": "longenough1"}).status_code == 200


def test_email_verification_flow():
    from app import mailer
    sent = []
    old_enabled, old_send = mailer.enabled, mailer.send
    mailer.enabled = lambda: True
    mailer.send = lambda to, subject, text: sent.append((to, text))
    try:
        c = TestClient(app)
        r = c.post("/api/auth/register", json={"agree": True, "age18": True, "email": "verify@example.com", "password": "longenough1"})
        assert r.status_code == 200
        assert len(sent) == 1 and sent[0][0] == "verify@example.com"
        code = sent[0][1].split("code is: ")[1][:6]
        me = c.get("/api/auth/me").json()
        assert me["email_verification_required"] is True and me["email_verified"] is False
        assert c.post("/api/auth/verify-email", json={"code": "000000" if code != "000000" else "111111"}).status_code == 400
        assert c.post("/api/auth/verify-email", json={"code": code}).status_code == 200
        assert c.get("/api/auth/me").json()["email_verified"] is True
        assert c.post("/api/auth/resend-verification").json()["already"] is True
    finally:
        mailer.enabled, mailer.send = old_enabled, old_send


def test_email_verification_attempts_capped():
    c = _mk("verifycap@example.com")
    with accounts.Conn() as conn:
        uid = conn.run("SELECT id FROM users WHERE email=?", ("verifycap@example.com",))[0]["id"]
    accounts.create_email_verification(uid)
    for _ in range(5):
        assert c.post("/api/auth/verify-email", json={"code": "999999" if accounts.hash_token("999999") else "999999"}).status_code == 400
    assert c.post("/api/auth/verify-email", json={"code": "999999"}).status_code == 400
    assert "Too many" in c.post("/api/auth/verify-email", json={"code": "999999"}).json()["detail"]
    # resend resets the counter (mailer disabled in tests -> auto-verifies instead)
    assert c.post("/api/auth/resend-verification").status_code == 200
    assert accounts.is_email_verified(uid)


def test_no_smtp_means_auto_verified():
    c = _mk("nosmtp@example.com")
    me = c.get("/api/auth/me").json()
    assert me["email_verification_required"] is False
    assert me["email_verified"] is True
