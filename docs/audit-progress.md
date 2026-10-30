# MockRep audit progress (not a completion certificate)

## New 27-item batch
1. PII logs: application errors log type/count only; mail exceptions no longer log tracebacks. Automatic client crash text collection removed. Reverse-proxy/access logs still need a query-string/retention audit.
2. Safe errors: generic 500 and custom HTML 404 already present; validation responses still need a comprehensive sensitive-input reflection review.
3. Bot limits: auth/signup/IP/AI limits already exist; endpoint-by-endpoint coverage review open.
4. IDOR: saved-history and recruiter isolation tests exist; guest interview sessions use unguessable bearer IDs, not account-bound ACLs. Account data access and guest-token disclosure still need attacker-view review.
5. Form validation: bounded Pydantic inputs, honeypot and rate limits already present. Every public form consent review open.
6. Renders: targeted browser flow showed no page exceptions; flicker review incomplete.
7. Upload-on-selection: implemented in app.js file.onchange, posts directly to /api/extract (server reads in memory, file not stored). DONE: visible consent note added next to the control and verified present before file selection in a real browser run (c44c8aa).
8. Design system: shared CSS tokens/components already present; full-page review open.
9. Animations: reduced-motion support already present; performance profiling open.
10. Horizontal scroll: toolbar regression fixed. Four widths, six views checked; remaining public pages/open states pending.
11. Accessibility: labels/focus indicators/reduced motion present. DONE (c44c8aa): automated audit of all nine pages - lang, title, meta description, og tags, h1, img alt, input labels, internal links, sitemap routes, 404 page: no fails. Still pending: contrast-ratio computation and full keyboard-only walkthrough.
12. Indexes: added session-user/expiry and user-org/Google-sub indexes. Full query-plan audit pending.
13. Cache hardening: per-key singleflight already present for AI lookups; malformed session IDs now rejected before DB access. Valid-looking absent IDs still query DB intentionally, so another worker's newly created session is not hidden by a stale negative cache. Hot-key/DB load testing open.
14. Load check: 1000 local concurrent ASGI /health tasks, all 200. See local-load-check.json. NOT evidence for DB, AI, socket or production capacity; full launch load test pending.
15. Admin baseline: existing token-protected report moderation and recruiter organization roles. User block/verify, broadcast and broader admin functions not implemented. Scope/least-privilege design pending; no public admin route added casually.
16. HTTPS/cookies/analytics: HTTPS live; cookie page exists; analytics request collection now disabled. Cookie copy/actual cookie inventory final review pending.
17. Launch hygiene: sitemap, robots, custom 404 and favicon exist. DONE (c44c8aa): canonical+og tags added to all public pages, offline.html description+noindex, screen.html description; all internal links and sitemap URLs verified 200 against a live local server. Pending: image weight and speed audit.
18. Form consent: signup consent and age gate present. Other forms pending review.
19. Claims/assets: factuality backstops already present. Full content/licensing sweep pending.
20. Terms: public terms existed; separate private draft copy pending.
21. Trademark: not searched yet; no availability claim.
22. Data safety: draft exists; final exact-build declaration pending.
23. Identity trio: source package com.ranjitsahoo.mockrep, versionCode 7. Registered Play identity and actual signed artifact certificate not yet checked for this source.
24. SEO/content: keyword research, 30-day plan, internal-link and Search Console draft pending. No submission.
25-27. Premium-only: prototype quarantined OFF. Pricing/token binding, subscriptions/lifecycle, reminders, refund page and payment/refund/failure admin tracking are NOT release-ready. No payment enabled.

## PDF output verification (c44c8aa)
Real Chrome print-to-PDF through the actual UI flows: prep pack, interview report, resume builder. Found and fixed a real launch bug: prep/report prints were BLANK because #prArea sat inside .wrap/#work, which the print CSS hides with display:none!important. Moved #prArea to a top-level body child; all three PDFs now render correct content (visually inspected page images). Immediate PDF upload extraction also verified end-to-end (pypdf parses an uploaded PDF into the resume box).

## Evidence discipline
253 server tests were passing before cache guard additions; 260 pass after them. Local Python3.10 used compatible installed package versions, not an exact production-lock install. Production Docker Python3.11 dependency installation succeeded on Render for the deployed source. Browser checks are targeted, not six whole-app rounds. No Play publication or billing activation.

## Six whole-app rounds as different users (2026-10-30, local mock-mode server, real Chrome via puppeteer-core; scripts in tests/visual/)
Requirement: "6+ test and security rounds as different users before handover; verify every button yourself."
1. Guest full journey (1366px): cookie bar, sample buttons, waitlist signup, all 12 tool tabs switch, 5-question interview WITH follow-ups completed (10 answers), session report shown; report/prep/builder print-to-PDF captured and text-verified with pypdf (57KB/49KB/26KB, real content - blank-print regression covered). PASS, no console/page errors.
2. Account user: bad-email, short-password, consent and age gates all reject with the right messages; register, history-tab gating, logout (private draft cleared), wrong-password reject, correct login, session persists across reload. PASS.
3. Signed-in power user: interview saved to My History (progress entry verified); resume review, JD match, STAR, company brief, negotiation start+reply, question bank, coding open/evaluate/hint, resume builder with experience entry all render. PASS.
4. Mobile user (390x844): zero horizontal overflow on landing and all 12 tool views, interview start + answer + feedback at mobile width, account drawer opens, no overflow. PASS.
5. Attacker: bogus/traversal/script session IDs all clean 404 (no internals leaked); XSS answer payload escaped in feedback HTML; oversized answer 422; login rate limit 429; card-token guess 404; /api/history 401 unauthenticated. Admin endpoint returns 404 without the admin token BY DESIGN (endpoint concealment, verified in source). Guest session state readable only with the unguessable 96-bit bearer ID (documented secret-link design) - NOTE: bearer IDs travel in URL paths, so reverse-proxy access-log scrubbing/retention stays on the open-items list.
6. Keyboard-only + reduced-motion user: reduced motion zeroes animation/transition durations; skip link is first tab stop and moves focus; 60-stop Tab walk - every stop visible with a focus indicator, no hidden focus, no traps; interview start + answer completed by keyboard only; Escape closes the nav drawer (verified at 390px). The account panel is an inline collapsible form, not a dialog, so Escape does not apply to it. PASS.
260 server tests still pass after these rounds.
