# MockRep premium plan - NOT READY, NOT ENABLED

Owner decision, 2026-10-30 04:46 IST:
- At Play launch all features are free for the first 2-3 months, with no charges anywhere.
- Later prices: yearly INR 499; lifetime INR 999. No monthly product.
- Premium must be a separate build, never included in the free-launch build.
- Ads and payments remain OFF. No Play publication is authorized.
- Exact activation date remains undecided. Do not start billing automatically.

The premium-billing branch is a prototype, not a release. It must not be enabled.
The free-launch Android manifest has no billing permission or billing SDK.

Before premium is ready:
- Bind each Play token to the authenticated account and reject replay across accounts.
- Validate product, package, account binding, purchase state and expiry from Google's response.
- Reject missing fields, canceled/refunded purchases and expired subscriptions; recheck revocations.
- Grant paid-through access when auto-renewal is canceled, without charging again.
- Acknowledge verified purchases through the supported Play flow.
- Add a working cancellation-management link and implement the 24-hour renewal notice, not merely its copy.
- Prices displayed must come from Play product details and match INR 499 yearly / INR 999 lifetime.
- Finish six independent end-to-end and security rounds including adverse cases.
- Obtain owner approval for activation timing and confirm the product setup in Play Console.

No payment-method or purchase testing against real money is authorized by this plan.
