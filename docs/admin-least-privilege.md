# Admin least-privilege design (design only - no public admin route shipped)

## Current admin surface (inventory)
| Surface | Gate | Behavior without valid credential |
| --- | --- | --- |
| POST /api/admin/block-card | ADMIN_TOKEN env, hmac.compare_digest on x-admin-token header, rate-limited | 404 (endpoint concealment, verified in round 5) |
| Recruiter organization roles | account + org membership | candidate data isolated by org; server tests cover isolation |
| Report/share-card moderation | same block-card token | public card 404s after block |

## Principles
1. No admin UI route on the public app. Admin actions stay CLI/API-with-token only until a real need exists; a casually added public admin panel is the worst-case attack surface.
2. Tokens live only in host env (Render dashboard), never in the repo, never in the client.
3. Constant-time comparison for every credential check (hmac.compare_digest already in use).
4. Conceal, don't advertise: 404 on auth failure, never 401/403 which confirms the route exists.
5. Every admin action writes an audit row (who-token-hash, action, target, ts, ip) before executing.

## Proposed roles when admin grows (least privilege)
| Role | Can | Cannot | Token storage |
| --- | --- | --- | --- |
| moderator | block/unblock share cards, view reported content | touch user accounts, see credentials, broadcast | separate MOD_TOKEN env |
| support | look up a user BY the user's own request (email given to support), trigger password-reset email, read audit log | change data, block users, export bulk data | separate SUPPORT_TOKEN env |
| admin | rotate the above tokens, user block/verify, broadcast | read passwords (impossible - argon2 hashes), read resume content without user consent flow | ADMIN_TOKEN env, rotated quarterly |

## Rules
- One token per role per env; never shared between people - person identity goes in the audit row via a per-person suffix header.
- Tokens rotated on any suspicion, quarterly otherwise; old tokens die immediately (single env value, no grace list).
- Broadcast (if ever built) is dry-run-first: counts only, explicit second call to send, rate-limited per day.
- User block/verify (not built) must be soft-delete style: reversible, reason required, audit logged.
- Bulk export is never an admin feature. GDPR/DPDP access requests are served per-user with the user's own verified session, not by an admin pulling data.

## Open items (deferred deliberately)
- User block/verify, broadcast, admin audit-log viewer: NOT implemented. Each needs its own review before any code.
