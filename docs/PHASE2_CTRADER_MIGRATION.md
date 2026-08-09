# Phase 2 — cTrader market-data migration

Date: 2026-08-10

## Decision

Agent 02 no longer uses Twelve Data for runtime market data. The runtime provider is now cTrader Open API using Spotware's official `ctrader-open-api` Python SDK.

## Runtime contract

Required secrets/variables:

- `CTRADER_CLIENT_ID`
- `CTRADER_CLIENT_SECRET`
- `CTRADER_ACCESS_TOKEN`
- `CTRADER_ACCOUNT_ID`

Optional:

- `CTRADER_ENVIRONMENT` (`demo` by default; `live` when explicitly configured)
- `CTRADER_SYMBOL` (`XAUUSD` by default)

The provider resolves the broker-specific symbol ID from the authenticated account, retrieves M5/M15/H1/H4 historical trendbars over one connection, and normalizes cTrader relative prices/timestamps into the existing canonical candle contract.

## Safety boundary

This integration is **market-data-only**. It does not submit, modify, close or manage orders or positions. Agent 05 remains the final permission authority and Agent 06 remains read-only with `execution_enabled: false`.

## Observation cadence

The Agent 02 workflow is aligned to the Phase 2 15-minute weekday observation cadence. The workflow installs the pinned cTrader SDK and reads credentials only from GitHub Actions secrets/variables.

## Validation gates

1. Exact-head deterministic CI must pass on the migration branch.
2. GitHub Actions must have valid cTrader credentials configured.
3. A credentialed Agent 02 run must produce timestamped XAUUSD M5/M15/H1/H4 state artifacts.
4. Only after representative runtime timestamps exist should outcome lateness tolerance be derived.

Synthetic tests are not treated as live timing evidence.
