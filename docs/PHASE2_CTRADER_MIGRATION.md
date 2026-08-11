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

Optional repository variables:

- `CTRADER_ENVIRONMENT=demo` (default)
- `CTRADER_SYMBOL=XAUUSD` (default)

`CTRADER_TOKEN_URL` is not consumed by the current runtime. cTrader's token endpoint is a fixed API endpoint used to exchange an authorization code or refresh token; the resulting access token is what the Open API connection uses for account authentication.

## Runtime scope

The implementation is strictly market-data-only. It does not submit orders, modify positions, or grant trading permissions.

## Validation sequence

1. Exact-head deterministic CI must pass.
2. Credentialed cTrader **demo** run must authenticate successfully.
3. Agent 02 must resolve the broker's XAUUSD symbol dynamically.
4. M5/M15/H1/H4 historical trendbar artifacts must be produced.
5. Repeated 15-minute observation runs must produce timestamped evidence.
6. Only representative operational samples may be used to derive timing/lateness tolerance.

Synthetic tests do not count as operational observation evidence.
