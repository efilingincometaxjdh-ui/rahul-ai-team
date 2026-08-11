# Rahul AI Team

Multi-agent market-intelligence and decision architecture with strict evidence and execution boundaries.

## Phase 2 market-data runtime

Agent 02 uses cTrader Open API as the authoritative XAUUSD broker market-data provider. Twelve Data is removed from the active runtime. Binance is available as supplemental public crypto telemetry only and is not an XAUUSD evidence source.

### cTrader runtime configuration

Required GitHub Actions repository secrets:

- `CTRADER_CLIENT_ID`
- `CTRADER_CLIENT_SECRET`
- `CTRADER_ACCESS_TOKEN`

Optional repository secret:

- `CTRADER_ACCOUNT_ID` — when absent, the provider selects the first account granted to the access token.

Optional repository variables:

- `CTRADER_ENVIRONMENT` (`demo` by default)
- `CTRADER_SYMBOL` (`XAUUSD` by default)

The runtime is read-only market data. No order, position, or execution operations are implemented by Agent 02.

## Safety boundary

Agent 05 remains the final permission authority. Agent 06 remains read-only with `execution_enabled=false`.

## Phase 2 validation

Deterministic CI must pass before merge. Credentialed demo runtime validation must then produce real M5/M15/H1/H4 XAUUSD observations before operational timing/lateness evidence can be claimed.
