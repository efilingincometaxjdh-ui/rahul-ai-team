# Phase 2 cTrader Market-Data Migration

## Source of truth

Agent 02 uses cTrader Open API as the authoritative XAUUSD broker market-data source. Twelve Data is not used by the active runtime.

Binance remains supplemental crypto telemetry only and must not be substituted for XAUUSD observation evidence.

## Authentication

The runtime follows Spotware's OAuth/account authentication flow:

1. cTrader application authentication with `clientId` and `clientSecret`.
2. Account discovery with the access token.
3. Account authentication using the selected `ctidTraderAccountId` and access token.
4. Symbol discovery and historical trendbar requests.

### GitHub Actions secrets

Required:

- `CTRADER_CLIENT_ID`
- `CTRADER_CLIENT_SECRET`
- `CTRADER_ACCESS_TOKEN`

Optional:

- `CTRADER_ACCOUNT_ID` — if omitted, Agent 02 selects the first account granted to the access token.

Non-secret configuration should use GitHub Actions variables where appropriate:

- `CTRADER_ENVIRONMENT=demo` (default)
- `CTRADER_SYMBOL=XAUUSD` (default)

`CTRADER_TOKEN_URL` is not a credential and is not required by the current runtime. The cTrader token endpoint is a fixed API endpoint used when exchanging an authorization code or refreshing a token; the resulting access token is the secret consumed by the market-data connection.

## Runtime scope

The implementation is strictly market-data-only. It does not submit orders, modify positions, or grant trading permissions.

The intended Phase 2 validation sequence is:

`CI -> credentialed demo run -> M5/M15/H1/H4 artifacts -> repeated observation samples -> timing/lateness measurement`

Synthetic tests do not count as operational observation evidence.
