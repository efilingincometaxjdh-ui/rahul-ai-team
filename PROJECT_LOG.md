# PROJECT LOG

## 2026-08-10 — cTrader authentication flow hardening

PR #27 now follows the official cTrader Open API account-authentication sequence: application authentication, account discovery by access token, account authentication, then symbol/trendbar requests.

`CTRADER_ACCOUNT_ID` is optional. When omitted, the provider selects the first account granted to the access token; when supplied, it must match an account granted to that token.

The runtime remains read-only and demo-first. No execution operations are implemented.

The repository requires `CTRADER_CLIENT_ID`, `CTRADER_CLIENT_SECRET`, and `CTRADER_ACCESS_TOKEN` for credentialed runtime validation. `CTRADER_TOKEN_URL` is configuration metadata rather than a credential and is not consumed by the current runtime.

Next gate: exact-head CI, then credentialed demo execution of Agent 02 to produce real M5/M15/H1/H4 XAUUSD observation artifacts.
