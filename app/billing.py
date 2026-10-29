"""Premium billing via Google Play. DISABLED unless BILLING_ENABLED=true.

Zero-cost design: the Android TWA uses the Digital Goods API (no SDK, no fees
beyond Play's), and the server verifies every purchase token with the Google
Play Developer API before granting an entitlement. Client-supplied tokens are
never trusted on their own (27-point checklist item 24).

Env:
  BILLING_ENABLED=true
  GOOGLE_PLAY_SERVICE_ACCOUNT_JSON=<service account JSON with androidpublisher scope>
"""
import json
import logging
import os
import time
import urllib.request

log = logging.getLogger("interviewpilot")

# Security hold: this prototype must never be enabled by an environment change.
# Remove this hold only after account/token binding, acknowledgment, lifecycle
# verification and six independent end-to-end/security rounds are implemented.
ENABLED = False
PACKAGE = "com.ranjitsahoo.mockrep"
PRODUCTS = {
    "mockrep_premium_yearly": "subscription",
    "mockrep_premium_lifetime": "inapp",
}
_ACTIVE_SUB_STATES = {"SUBSCRIPTION_STATE_ACTIVE", "SUBSCRIPTION_STATE_IN_GRACE_PERIOD"}


def _service_token() -> str:
    raw = os.environ.get("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON", "")
    if not raw:
        raise RuntimeError("billing service account not configured")
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request as GRequest
    creds = service_account.Credentials.from_service_account_info(
        json.loads(raw), scopes=["https://www.googleapis.com/auth/androidpublisher"])
    creds.refresh(GRequest())
    return creds.token


def _play_get(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def _grant(user_id: str, plan_id: str, expiry_at, source: str) -> None:
    from app import accounts
    with accounts.Conn() as c:
        c.run(
            "INSERT INTO entitlements (user_id, plan_id, state, expiry_at, source, last_verified_at, schema_version) "
            "VALUES (?,?,?,?,?,?,1) "
            "ON CONFLICT(user_id) DO UPDATE SET plan_id=EXCLUDED.plan_id, state=EXCLUDED.state, "
            "expiry_at=EXCLUDED.expiry_at, source=EXCLUDED.source, last_verified_at=EXCLUDED.last_verified_at",
            (user_id, plan_id, "active" if (expiry_at is None or expiry_at > time.time()) else "expired",
             expiry_at, source, time.time()),
        )
        c.run("UPDATE users SET plan=? WHERE id=?", (plan_id, user_id))


def verify_purchase(user_id: str, product_id: str, purchase_token: str) -> dict:
    """Verify a Play purchase server-side and grant the entitlement. Returns the record."""
    if not ENABLED:
        raise PermissionError("Billing is not enabled.")
    kind = PRODUCTS.get(product_id)
    if not kind:
        raise ValueError("Unknown product.")
    token = _service_token()
    if kind == "subscription":
        data = _play_get(
            f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{PACKAGE}"
            f"/purchases/subscriptionsv2/tokens/{purchase_token}", token)
        state = data.get("subscriptionState", "")
        if state not in _ACTIVE_SUB_STATES:
            raise PermissionError(f"Subscription is not active ({state}).")
        expiry_ms = (data.get("lineItems") or [{}])[0].get("expiryTime")
        if expiry_ms:
            from datetime import datetime
            expiry_at = datetime.fromisoformat(expiry_ms.replace("Z", "+00:00")).timestamp()
        else:
            expiry_at = None
        _grant(user_id, "premium", expiry_at, "play")
    else:
        data = _play_get(
            f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{PACKAGE}"
            f"/purchases/products/{product_id}/tokens/{purchase_token}", token)
        if data.get("purchaseState", 0) != 0:
            raise PermissionError("Purchase is not completed.")
        _grant(user_id, "premium", None, "play")
    from app import accounts
    with accounts.Conn() as c:
        rows = c.run("SELECT plan_id, state, expiry_at, source FROM entitlements WHERE user_id=?", (user_id,))
    return rows[0] if rows else {}
