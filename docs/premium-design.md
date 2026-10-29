# MockRep Premium - design (billing DISABLED by default)

Status: prepared, not active. Payments stay OFF until Ranjit explicitly turns them on.
One switch turns it on: set `BILLING_ENABLED=true` on the server + publish the Android
update with billing support + activate the products in Play Console. No code push needed.

## Architecture (zero recurring cost)
- Android TWA wrapper uses the Digital Goods API (`getDigitalGoodsService`); no extra SDK.
  The only manifest change is `<uses-permission android:name="com.android.vending.BILLING" />`.
- Client calls `POST /api/billing/verify` with the purchase token. The server verifies it
  with the Google Play Developer API (`purchases.subscriptionsv2.get` / `purchases.products.get`)
  using a Play service account before granting entitlement. Purchase tokens are never trusted
  from the client alone (checklist item 24).
- Entitlements live in the existing `entitlements.py` record (`plan=premium`), expiry from the
  Play response. Existing `users.plan` column already supports it.
- Web (non-Play) purchases: NOT planned - Play app only, so no card processing, no refunds to
  manage, no Stripe fees. Free web tier stays as-is.

## Cancellation (Play policy + Ranjit's item 11)
- The paywall and the account drawer always show: "Cancel anytime: Play Store > Profile >
  Payments & subscriptions" with a direct link to
  https://play.google.com/store/account/subscriptions
- Cancellation never locks the user out early: entitlement lasts to the paid-through date
  from Google's response.
- 24-hour pre-renewal notice: the server stores the next renewal time from the Play API; the
  push-reminder worker (same web-push infra as practise reminders) sends "Your MockRep Premium
  renews tomorrow - manage it here" 24h before. Google also emails receipts at each charge.

## Refunds & price display
- Prices shown only from the Play Billing SKU details (local currency), never hardcoded.
- Refund policy line on the paywall: handled by Google Play's standard refund flow; link shown.

## Data safety
- Play processes payment data; MockRep never sees card details. Data safety form updated to
  reflect purchase history when enabled.
