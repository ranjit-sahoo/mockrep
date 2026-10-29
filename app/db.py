"""Interview and negotiation session storage.

Uses the same database as accounts: Postgres when DATABASE_URL is set (so an interview in progress survives
restarts and deploys on the free host), SQLite otherwise (local runs and tests).
"""
import json
import re
import threading
import time
import uuid

from app import accounts

TTL_SECONDS = 2 * 24 * 3600  # guest sessions hold resume text; keep it short
_PRUNE_EVERY = 600  # seconds between cleanups of expired sessions
_ready = False
_last_prune = 0.0
_lock = threading.Lock()


def _ensure(c):
    global _ready
    if _ready:
        return
    with _lock:
        c.run("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, data TEXT NOT NULL, created DOUBLE PRECISION NOT NULL DEFAULT 0)"
              if accounts.using_postgres() else
              "CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, data TEXT NOT NULL, created REAL NOT NULL DEFAULT 0)")
        if not accounts.using_postgres():
            cols = [r["name"] for r in c.run("PRAGMA table_info(sessions)")]
            if "created" not in cols:  # databases made by the older session store
                c.run("ALTER TABLE sessions ADD COLUMN created REAL DEFAULT 0")
        c.run("CREATE INDEX IF NOT EXISTS sessions_created ON sessions (created)")
        _ready = True


def create(data: dict) -> str:
    global _last_prune
    sid = uuid.uuid4().hex[:24]
    now = time.time()
    with accounts.Conn() as c:
        _ensure(c)
        c.run("INSERT INTO sessions (id, data, created) VALUES (?, ?, ?)", (sid, json.dumps(data), now))
        if now - _last_prune > _PRUNE_EVERY:
            _last_prune = now
            c.run("DELETE FROM sessions WHERE created > 0 AND created < ?", (now - TTL_SECONDS,))
    return sid


def load(sid: str):
    # Session IDs are generated as 24 lowercase hex chars. Malformed misses
    # must not reach the database. Well-formed misses still require a lookup:
    # negative-caching them would hide sessions created by another worker.
    if not isinstance(sid, str) or not re.fullmatch(r"[0-9a-f]{24}", sid):
        return None
    with accounts.Conn() as c:
        _ensure(c)
        c.run("DELETE FROM sessions WHERE created <= 0 OR created < ?", (time.time() - TTL_SECONDS,))
        rows = c.run("SELECT data FROM sessions WHERE id=? AND created >= ?", (sid, time.time() - TTL_SECONDS))
    return json.loads(rows[0]["data"]) if rows else None


def save(sid: str, data: dict):
    if not isinstance(sid, str) or not re.fullmatch(r"[0-9a-f]{24}", sid):
        return None
    with accounts.Conn() as c:
        _ensure(c)
        c.run("UPDATE sessions SET data=? WHERE id=?", (json.dumps(data), sid))
