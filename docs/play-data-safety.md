# Google Play Data safety form - exact answers for MockRep

Last reviewed: October 30, 2026 (matches /privacy section 3A). Tick these in Play Console > App content > Data safety.

## Top-level
- Does your app collect or share any of the required user data types? **Yes**
- Is all user data encrypted in transit? **Yes** (HTTPS only)
- Do you provide a way for users to request that their data is deleted? **Yes**
  - Deletion URL: https://mockrep.onrender.com/delete-account
  - In-app: My history > Delete account (and Menu > Delete account)

## Data types

### Personal info
- **Email address**: Collected = Yes, Shared = No. Purpose: App functionality, Account management. Optional = Yes (guest mode works without an account; required only to create one). Processed ephemerally = No. Encrypted in transit; users can delete.
- **Name**: Collected = Yes, Shared = No. Purpose: App functionality. Optional = Yes. (Only for recruiter screening candidates, entered by the candidate or their recruiter; share cards use a user-typed display name.) Users can delete.
- **Phone number**: Collected = Yes, Shared = No. Purpose: App functionality. Optional = Yes. (Recruiter screening candidates only, and recruiters adding candidates to their own pipeline.) Deleted automatically after the recruiter-chosen retention (7-90 days).
- **User IDs**: Collected = Yes, Shared = No. Purpose: Account management. Optional = Yes. (Internal account ID; Google account ID when using Google sign-in.)

### Files and docs
- **Files and docs**: Collected = Yes, Shared = No. Purpose: App functionality. Optional = Yes. (Resume PDF/DOCX uploads and pasted resume/JD text.) Guest uploads deleted within 2 days; saved items deleted with the account.

### App activity
- **App interactions**: Collected = Yes, Shared = No. Purpose: App functionality. Optional = No for server-side saved scores (only what a signed-in user chooses to save). Users can delete saved items. (First-party aggregate visit counting exists in code but is disabled in the launch build - no analytics data is collected at all; declare Analytics purpose only if it is ever enabled.)

### App info and performance
- Crash logs / Diagnostics: **Not collected** (no crashlytics, no third-party analytics; first-party visit counting disabled in the launch build).

### Location, Health & fitness, Messages, Photos & videos, Audio, Calendar, Contacts, Financial info, Web browsing, Device or other IDs
- **Not collected**. (Microphone is used on-device for speech-to-text and local playback only; audio never leaves the device, so "Audio" = not collected. No ad ID, no Android ID collection.)

## Sharing
- No data is sold or shared with third parties for marketing or advertising.
- Submitted text (resume, job description, answers) is transferred to the AI provider (Nebius Token Factory) solely to produce the requested result - declare as "transferred to a service provider for app functionality" if the form asks about service providers.

## Other Play Console declarations (App content)
- **Ads**: No, the app does not contain ads.
- **Target audience and content**: Adults 18+. NOT designed for children (privacy policy states 16+; no child-directed content, so Families policy does not apply).
- **Privacy policy URL**: https://mockrep.onrender.com/privacy
- **News apps / COVID / Government apps**: No.
- **Data deletion URL** (Account deletion section): https://mockrep.onrender.com/delete-account
