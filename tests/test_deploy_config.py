"""Deployment configuration guards: the app runs behind Render's load balancer,
so uvicorn must trust proxy headers or every request.client.host is a rotating
proxy IP and all per-client rate limiters are silently defeated (found by the
live security battery: 80 requests in 3.4s drew no 429)."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_uvicorn_trusts_proxy_headers():
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "--proxy-headers" in dockerfile
    assert "--forwarded-allow-ips" in dockerfile


def test_rate_limiter_trips_at_limit():
    from app.guard import RateLimiter
    rl = RateLimiter(limit=3, window=60.0)
    assert rl.check("k") and rl.check("k") and rl.check("k")
    assert not rl.check("k")
    assert rl.check("other")


def test_fail_limiter_locks_after_limit():
    from app.guard import FailLimiter
    fl = FailLimiter(limit=2, window=60.0)
    assert not fl.blocked("acct")
    fl.fail("acct")
    fl.fail("acct")
    assert fl.blocked("acct")
