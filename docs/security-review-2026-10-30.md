# Security/privacy review batch (2026-10-30)

Closes the review-only items from the 27-item audit list. Each entry: what was checked, what was found, what changed.

## 1. PII in logs
- Application logging already emits types and counts only (llm.py logs model + error type + status; main.py logs exception type; no user content).
- FOUND + FIXED: uvicorn access logs wrote full URL paths, and guest-session bearer IDs travel in paths (/api/session/<sid>/...). A new `_AccessLogSidFilter` masks the 24-char session ID (`/api/session/***/state`) before records are written. Verified live: zero occurrences of a real session ID in the log file after requests.
- Residual (outside this repo): Render's own proxy/platform logs are Render-managed; recommend keeping Render log retention at its default and not exporting raw logs anywhere.
- Regression tests: tests/test_validation_privacy.py::test_access_log_filter_masks_session_id (and a non-matching-path guard).

## 2. Safe error responses
- Audited every HTTPException detail string in app/: none echo user input.
- FOUND + FIXED: FastAPI's default 422 handler reflected the offending `input` value back in the response. Confirmed with a 300-char password returned verbatim. A custom `RequestValidationError` handler now returns only type/loc/msg. Verified live: oversized password no longer present in the response.
- Regression tests: test_422_does_not_reflect_password_value, test_422_still_reports_field_and_reason.

## 3. Bot/limit coverage
- Enumerated all POST routes: 38/38 in main.py and 13/13 in hub.py carry explicit rate-limit dependencies (IP limits, auth limits, or per-account AI caps). No unguarded mutation route.

## 5 + 18. Forms and consent sweep
- Signup: 18+ age checkbox and Terms/Privacy checkbox, both enforced client-side with clear messages; server stores consent.
- Google sign-in: consent enforced via the mr_gconsent marker cookie.
- File upload: visible note at the control that the file is sent once to read text and is not stored (added c44c8aa).
- Guests: no account, no marketing email; resume-text 2-day retention disclosed in the FAQ and Privacy Policy. Waitlist collects email only with a no-spam note.
- No public form collects data without an adjacent disclosure.

## 8 + 9. Design system and animation review
- Shared CSS tokens/components across pages (verified during the six whole-app rounds and round 6's dedicated pass).
- prefers-reduced-motion zeroes animation/transition durations (verified in round 6 in real Chrome).
- No animation-driven layout thrash observed in the round scripts (no long-task or overflow failures at 4 widths).

## 13. Cache hot-key check
- No cache layer exists beyond per-key singleflight on AI lookups and an lru_cache on icon generation; nothing else to hot-key. DB-backed load results in docs/local-load-check-db.json cover the current risk.

## 16. Cookie inventory
- ip_session: HttpOnly, SameSite=Lax, Secure on HTTPS, 30 days, documented.
- mr_gconsent: 10-minute consent marker for Google sign-in.
- FIXED: cookies.html now documents mr_gconsent (it previously listed only ip_session).

## 19. Claims and third-party assets sweep
- Visible-text sweep of all public pages for unsupported claims (guarantee/#1/best/certified/etc.): only the existing disclaimer ("AI feedback and salary figures are estimates, not guarantees") and HTML entities matched. No unsupported claims.
- No CDN/third-party JS, CSS, or font references: everything is self-hosted, fonts are system stacks, so no third-party web-asset licensing obligations. Python dependencies are standard permissive-licensed packages (MIT/BSD/Apache).
