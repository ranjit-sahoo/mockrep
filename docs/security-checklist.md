> DRAFT inventory, not certification. Assertions below need independent source review and six end-to-end test rounds. Pattern scans do not prove absence of all secrets.

# MockRep 27-point security checklist (web app + API)

Mapped item by item, with where each control lives. Last audited: 2026-10-30.

| # | Point | Status | Where |
|---|-------|--------|-------|
| 1 | Hide secrets | Implemented, review pending | No secrets in repo; all via env vars; vault-held deploy secrets |
| 2 | Env vars | Implemented, review pending | `os.environ.get(...)` everywhere; no defaults with real values |
| 3 | Git-history leak check | Implemented, review pending 2026-10-30 | Full `git log -p` scan for token/key patterns: clean |
| 4 | Protect admin pages | Implemented, review pending | Admin token (`ADMIN_TOKEN`) for moderation; role_gate middleware separates recruiter/candidate APIs |
| 5 | Secure auth | Implemented, review pending | Email+password, Google ID-token verify, honeypot, signup/day caps, FailLimiter on login |
| 6 | Per-user data permissions | Implemented, review pending | Every history/progress/recruiter query is scoped by `user_id`/`org_id`; isolation tests in test_accounts.py, test_hub.py |
| 7 | Secure sessions/tokens | Implemented, review pending | Random tokens, stored SHA-256 hashed, HttpOnly + SameSite=Lax cookies, expiry, logout + logout-all; change-password revokes other sessions |
| 8 | Input validation | Implemented, review pending | Pydantic `Field(max_length=...)` on every body model; role/enum checks server-side |
| 9 | XSS | Implemented, review pending | No `dangerouslySetInnerHTML`-style injection; client builds DOM with textContent; CSP `script-src 'self'` blocks inline scripts |
| 10 | SQL injection | Implemented, review pending | Parameterized queries only (`?` / `%s` placeholders); SQLi probe test in test_security_account.py |
| 11 | CSRF | Implemented, review pending | SameSite=Lax cookies + `request_origin_guard` middleware (Origin allowlist + `sec-fetch-site` cross-site block; GIS form post protected by Google's g_csrf_token double-submit) |
| 12 | Rate limiting | Implemented, review pending | Per-IP per-minute, auth per-minute, signup/day, AI per-IP/day, per-user AI/day, per-endpoint limiters |
| 13 | Secure every API endpoint | Implemented, review pending | `LIMITED` dependency on all routes; `need_user` on account routes; role gate; `USER_AI` per-account cap |
| 14 | CORS | Implemented, review pending | Off by default; opt-in via `CORS_ORIGINS` env allowlist |
| 15 | Security headers | Implemented, review pending | CSP, X-Content-Type-Options, X-Frame-Options DENY, Referrer-Policy, Permissions-Policy, HSTS in `security_headers` middleware |
| 16 | HTTPS | Implemented, review pending | Render terminates TLS; HSTS set; OAuth + cookies marked Secure |
| 17 | Debug off in production | Implemented, review pending | No debug flag in app; unhandled errors logged without request bodies, generic 500 to client |
| 18 | Update dependencies | Implemented, review pending 2026-10-30 | requirements.txt pinned with upper bounds; test_requirements_all_pinned_no_urls enforces it |
| 19 | Remove unused code/routes | Implemented, review pending | Dead routes pruned during build-3 cleanup; static mount exposes only app/static |
| 20 | No exposed .env/backup/config | Implemented, review pending 2026-10-30 | `git ls-files` scan: no .env/keys/pem/keystore tracked; static serving limited to app/static; no directory listing |
| 21 | Secure DB access | Implemented, review pending | Single app role, parameterized SQL, DATABASE_URL env-only, no remote DB port exposure |
| 22 | Passwords hashed (Argon2id) | Implemented, review pending 2026-10-30 | argon2-cffi (time=3, mem=64MB, par=2); legacy scrypt2 hashes verify and upgrade on login; dummy-hash timing equalization |
| 23 | Secure file uploads | Implemented, review pending | 5 MB cap, magic-byte sniffing (PDF/DOCX/DOC/TXT), 30-page cap, parse errors -> 400, never stored to disk |
| 24 | Payment/webhook signature verification | N/A now / designed | Payments OFF. Premium design (docs/premium-design.md) requires Play Developer API server-side verification before any entitlement grant |
| 25 | SSRF | Implemented, review pending | Server never fetches user-supplied URLs; outbound calls go only to fixed provider endpoints (LLM, Google tokeninfo) |
| 26 | Monitoring + backups | Implemented, review pending | First-party analytics counters (no PII); no automatic crash logging; copy-version diagnostic only; Render Postgres daily backups on paid / manual `pg_dump` documented for free; uptime via /health |
| 27 | Full re-audit after fixes | Implemented, review pending 2026-10-30 | 249-test suite incl. security batch; live E2E rounds for these changes have NOT yet been completed |

## Ongoing
- Re-run the secrets scan before every release: `git log -p | grep -E <patterns>` (patterns in repo root script `scripts/` to be added) — current scan clean.
- Rotate any credential that ever touches a chat, ticket, or log.
