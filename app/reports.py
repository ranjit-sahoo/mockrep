"""User reports of offensive AI-generated content (Google Play generative-AI policy).

Stored in the same database as accounts. Reports hold only what the user
chooses to send: the tool name, an optional reason and a short excerpt.
"""
import time
import uuid

from app import accounts


def _ensure(c):
    c.run(
        "CREATE TABLE IF NOT EXISTS content_reports (id TEXT PRIMARY KEY, kind TEXT NOT NULL, reason TEXT NOT NULL, excerpt TEXT NOT NULL, email TEXT NOT NULL DEFAULT '', created DOUBLE PRECISION NOT NULL)"
        if accounts.using_postgres()
        else
        "CREATE TABLE IF NOT EXISTS content_reports (id TEXT PRIMARY KEY, kind TEXT NOT NULL, reason TEXT NOT NULL, excerpt TEXT NOT NULL, email TEXT NOT NULL DEFAULT '', created REAL NOT NULL)"
    )


def add(kind: str, reason: str, excerpt: str, email: str = "") -> str:
    rid = uuid.uuid4().hex[:16]
    with accounts.Conn() as c:
        _ensure(c)
        c.run(
            "INSERT INTO content_reports (id, kind, reason, excerpt, email, created) VALUES (?, ?, ?, ?, ?, ?)",
            (rid, kind[:40], reason[:600], excerpt[:600], email[:200], time.time()),
        )
    return rid
