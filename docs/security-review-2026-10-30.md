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

## 4. IDOR / authorization review (second pass)
- History items: queries scoped by the authenticated user id; another user's item id returns 404 (isolation tests already existed).
- Recruiter campaigns/pipeline/audit: every access passes an org-ownership check (_mine).
- Guest interview + negotiation sessions: 96-bit random bearer ids (uuid4 hex[:24], verified in source), 404 without the id; documented secret-link design, now with masked access logs (item 1).
- Screening invite tokens: 192-bit secrets.token_urlsafe(24), compared with compare_digest.
- Share cards: HMAC-SHA256 signed payloads with compare_digest, plus a report/block moderation path.
- Catalog ids (coding problems, practice modules): unknown values 404 via _guard.
- Error details: all ValueError messages that reach 400 responses are static strings (audited accounts.py/services.py).
- Hardening note (not changed): card.py falls back to NEBIUS_API_KEY as the HMAC secret when CARD_SECRET is unset. Recommend setting a dedicated CARD_SECRET env var at a natural rotation point; changing it invalidates already-shared cards, so it was not flipped silently.

## 6. Render flicker
- Chrome layout-shift measurement: CLS 0 on / and 0.0002 on the screening page (threshold 0.1). No flicker. Reduced-motion path verified earlier in round 6.

## 10. Horizontal scroll, remaining pages
- Real-Chrome sweep of /, /about, /help, /terms, /privacy, /cookies, /delete-account, the screening page, the offline page and the 404 page at 1366/1024/768/390 px: zero horizontal overflow, zero unexpected console/page errors. (/hub and /screen are not pages: the hub is a view inside the main SPA and screening is served at /s/{token}; their 404s are correct.)

## 11. Contrast computation (leftover)
- Computed WCAG ratios from rendered colors in Chrome: body 16.9:1, muted/footer 7.7:1, h1 16.9:1, consent/FAQ text ~14:1 (alpha-composited), buttons/links on brand gradients 7.9:1 worst-case stop. All pass AA. Keyboard walkthrough was completed in round 6. Item fully closed.

## 12. Query-plan audit
- EXPLAIN QUERY PLAN on every hot query shape: history/auth_sessions/progress by user, users by email, campaigns by org, attempts by campaign/token, session lookup + prune sweep - all SEARCH via index or PK, no table scans. Attempts ORDER BY uses a temp b-tree; recruiter-scale tables, not hot. No changes needed.

## 17. Asset weight and speed
- DejaVuSans fonts (1.4MB) are server-side only (card PNG rendering), never referenced by web pages. Question packs are lazy-loaded on tab use. sw.js is no-cache, icons 1-day, static 5-min.
- FOUND + FIXED: responses were served uncompressed (Render/Cloudflare pass-through). Added Starlette GZipMiddleware (minimum_size=1000); app.js 91KB and index.html 51KB now compress (verified content-encoding: gzip locally).
