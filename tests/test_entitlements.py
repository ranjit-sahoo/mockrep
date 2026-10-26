"""Inert monetization seams: entitlement record defaults, corrupt/forward-version safety,
non-gating of privacy/export/deletion/security/reporting, and migration safety."""
import os
import sqlite3
import tempfile

os.environ.pop("NEBIUS_API_KEY", None)
os.environ.pop("DATABASE_URL", None)
os.environ["RATE_LIMIT_PER_MIN"] = "100000"
os.environ["AUTH_RATE_PER_MIN"] = "100000"
os.environ["SIGNUPS_PER_DAY"] = "100000"
os.environ["AI_DAILY_PER_IP"] = "100000"
os.environ["INTERVIEWPILOT_DB"] = os.path.join(tempfile.mkdtemp(), "ent.sqlite3")

from fastapi.testclient import TestClient

from app import accounts, entitlements
from app.main import app

accounts.SQLITE_PATH = os.environ["INTERVIEWPILOT_DB"]


def _user(c, email):
    r = c.post("/api/auth/register", json={"agree": True, "email": email, "password": "longenough1"})
    assert r.status_code == 200
    with accounts.Conn() as conn:
        return conn.run("SELECT id FROM users WHERE email=?", (email.lower(),))[0]["id"]


def _set_ent(uid, **cols):
    with accounts.Conn() as conn:
        conn.run("INSERT INTO entitlements (user_id, plan_id, state, source, schema_version) VALUES (?, ?, ?, ?, ?)",
                 (uid, cols.get("plan_id", "free"), cols.get("state", "free"),
                  cols.get("source", "none"), cols.get("schema_version", 1)))


def test_guest_and_missing_row_read_free():
    assert entitlements.record_for(None) == entitlements.ENT_DEFAULT
    assert entitlements.record_for({"id": "nobody"}) == entitlements.ENT_DEFAULT


def test_default_row_after_register():
    c = TestClient(app)
    uid = _user(c, "ent1@example.com")
    ent = entitlements.record_for({"id": uid})
    assert ent == entitlements.ENT_DEFAULT  # no row yet -> free default, nothing assigned
    me = c.get("/api/auth/me").json()
    assert me["entitlement"]["plan_id"] == "free" and me["entitlement"]["state"] == "free"
    assert me["ads"] == {"enabled": False}


def test_corrupt_and_forward_version_read_free():
    c = TestClient(app)
    uid = _user(c, "ent2@example.com")
    _set_ent(uid, plan_id="gold!!!", state="weird", source="teleport", schema_version=99)
    ent = entitlements.record_for({"id": uid})
    assert ent["plan_id"] == "free" and ent["state"] == "free"
    assert ent["source"] == "none" and ent["schema_version"] == 1
    # other stored data untouched
    with accounts.Conn() as conn:
        assert conn.run("SELECT email FROM users WHERE id=?", (uid,))[0]["email"] == "ent2@example.com"


def test_never_gated_surfaces_survive_revoked_state():
    c = TestClient(app)
    uid = _user(c, "ent3@example.com")
    _set_ent(uid, state="revoked", plan_id="free")
    # feature reader: always-allowed set wins in every state
    for f in ("privacy", "data_export", "account_deletion", "security", "reporting"):
        assert entitlements.allowed({"id": uid}, f) is True
    # live endpoints under revoked state: privacy page, data reads, reporting
    assert c.get("/privacy").status_code == 200
    assert c.get("/api/history").status_code == 200
    assert c.get("/api/progress").status_code == 200
    r = c.post("/api/content-report", json={"kind": "interview", "reason": "synthetic test report"})
    assert r.status_code == 200, r.status_code  # reporting must never be gated
    # account deletion still works
    assert c.delete("/api/auth/account").status_code == 200
    assert c.get("/api/auth/me").json()["user"] is None


def test_unknown_feature_and_plan_fall_back_to_free():
    c = TestClient(app)
    uid = _user(c, "ent4@example.com")
    _set_ent(uid, plan_id="platinum-typo")
    assert entitlements.allowed({"id": uid}, "interview") is True  # unknown plan -> free set
    assert entitlements.allowed({"id": uid}, "not-a-feature") is False  # unknown feature -> not silently granted


def test_entitlements_table_migration_is_additive():
    path = os.path.join(tempfile.mkdtemp(), "old.sqlite3")
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, pw_hash TEXT NOT NULL, created REAL NOT NULL)")
    con.execute("INSERT INTO users VALUES ('u-old', 'old@example.com', 'h', 1.0)")
    con.commit(); con.close()
    old_path = accounts.SQLITE_PATH
    accounts.SQLITE_PATH = path
    try:
        with accounts.Conn() as conn:
            assert conn.run("SELECT email FROM users WHERE id='u-old'")[0]["email"] == "old@example.com"
            conn.run("INSERT INTO entitlements (user_id) VALUES ('u-old')")  # table exists with defaults
            row = conn.run("SELECT plan_id, state, source, schema_version FROM entitlements WHERE user_id='u-old'")[0]
            assert (row["plan_id"], row["state"], row["source"], row["schema_version"]) == ("free", "free", "none", 1)
    finally:
        accounts.SQLITE_PATH = old_path
