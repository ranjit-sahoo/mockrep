"""Small in-memory per-client rate limiter (sliding window)."""
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self.hits = defaultdict(deque)
        self.lock = threading.Lock()

    def check(self, key: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        with self.lock:
            q = self.hits[key]
            while q and q[0] <= now - self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            if len(self.hits) > 5000:  # bound memory
                for k in [k for k, v in self.hits.items() if not v or v[-1] <= now - self.window]:
                    del self.hits[k]
            return True


import os

limiter = RateLimiter(limit=int(os.environ.get("RATE_LIMIT_PER_MIN", "60")), window=60.0)


def client_key(request: Request) -> str:
    """Use the transport peer after the server proxy middleware, never arbitrary headers."""
    # Uvicorn's configured proxy handling owns the transport peer. Do not
    # accept arbitrary CDN or X-Forwarded-For fields at the application layer.
    return request.client.host if request.client else "unknown"


# Anonymous abuse cap: each POST can trigger a paid model call, so cap them per client per day.
daily = RateLimiter(limit=int(os.environ.get("AI_DAILY_PER_IP", "250")), window=86400.0)


def rate_limit(request: Request):
    key = client_key(request)
    if os.environ.get("DATABASE_URL"):
        if not shared_limit("minute", key, limiter.limit, limiter.window) or (request.method=="POST" and not shared_limit("daily", key, daily.limit, daily.window)):
            raise HTTPException(429, "Usage limit reached or limits temporarily unavailable. Please try later.")
        return
    if not limiter.check(key):
        raise HTTPException(429, "Too many requests. Please wait a minute and try again.")
    if request.method == "POST" and not daily.check(key):
        raise HTTPException(429, "Daily free usage limit reached for this network. Please come back tomorrow.")


class FailLimiter:
    """Counts failures per key (e.g. an account) and blocks after `limit` within `window` seconds."""

    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self.hits = defaultdict(deque)
        self.lock = threading.Lock()

    def _prune(self, q, now):
        while q and q[0] <= now - self.window:
            q.popleft()

    def blocked(self, key: str) -> bool:
        now = time.monotonic()
        with self.lock:
            q = self.hits.get(key)
            if q is None:
                return False
            self._prune(q, now)
            return len(q) >= self.limit

    def fail(self, key: str):
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            self._prune(q, now)
            q.append(now)
            if len(self.hits) > 5000:
                for k in [k for k, v in self.hits.items() if not v or v[-1] <= now - self.window]:
                    del self.hits[k]


def shared_limit(name: str, key: str, limit: int, window: float) -> bool:
    """Database-backed limits survive workers/restarts; fail closed on outage."""
    from app import accounts
    import hashlib
    now = time.time()
    bucket = name + ':' + hashlib.sha256(key.encode()).hexdigest()
    try:
        with accounts.Conn() as c:
            c.run("CREATE TABLE IF NOT EXISTS request_limits (bucket TEXT PRIMARY KEY, since DOUBLE PRECISION NOT NULL, n INTEGER NOT NULL)")
            c.run("DELETE FROM request_limits WHERE since < ?", (now-172800,))
            rows=c.run("INSERT INTO request_limits(bucket,since,n) VALUES(?,?,1) ON CONFLICT(bucket) DO UPDATE SET since=CASE WHEN request_limits.since < ? THEN EXCLUDED.since ELSE request_limits.since END, n=CASE WHEN request_limits.since < ? THEN 1 ELSE request_limits.n+1 END RETURNING n", (bucket,now,now-window,now-window))
            return rows[0]['n'] <= limit
    except Exception:
        return False
