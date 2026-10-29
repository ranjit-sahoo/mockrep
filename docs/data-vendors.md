# Data vendors and regions (zero-cost constraint)

Minimal sharing by design; every vendor processes only what the feature needs.

| Vendor | What it gets | Why | Region notes |
|--------|--------------|-----|--------------|
| Render (hosting + Postgres) | All server-side data (account, history, progress) | Runs the app | Free tier; region chosen at creation - use the nearest free region (Singapore for India) |
| Nebius Token Factory (LLM) | Prompt text the user pastes (resume/JD) to generate answers | AI features | No account data sent; requests are per-call, not retained by us beyond the user's own saved history |
| Google (Sign-In) | Email + Google sub for users who choose Google login | Optional sign-in | Global |
| Google Play (future, premium only) | Purchase token + subscription state | Billing, disabled by default | Google-managed |
| SMTP relay (optional, if SMTP_HOST set) | Recipient email + 6-digit code | Email verification | Operator's choice; any free tier (e.g. Brevo) |

No analytics vendor, no ads SDK, no crash-reporting vendor: analytics collection is disabled, and no automatic crash details are stored.
