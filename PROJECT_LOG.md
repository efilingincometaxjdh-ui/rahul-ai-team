# Rahul AI Team — Project Log

Last audited: 2026-08-08
Branch: `main`
Phase: **Phase 2 — evidence infrastructure**

This file is the persistent source of truth for architecture, recovery evidence, current health, contracts, safety policy and next work.

## Loop Engineering protocol

**Inspect → Plan → Build → Test → Observe → Critique → Fix → Retest → Integrate → Monitor → Repeat**.

Rules:
- Repository evidence beats assumptions.
- Deterministic safety gates beat model opinions.
- Generated state uses the normalized atomic `utils/json_writer.py` envelope.
- Missing, malformed, failed, stale, future-dated or degraded upstream state reduces authority, never increases it.
- No autonomous execution/broker integration.
- Agent 05 fails closed on `NO_TRADE`, invalid input, unknown decision/risk states, invalid confidence, EXTREME risk and stale Agent 04 state.
- Agent 06 is read-only and always exposes `execution_enabled: false`.
- Historical/analytics infrastructure is evidence-only and must never increase trading authority.

## Architecture

`Agent 02 Technical` + `Agent 03 Macro/News` → **Agent 04 Decision** → **Agent 05 Permission** → **Agent 06 Alert Gateway (read-only)** → **Trader View / historical evidence**.

Agent 01 remains isolated. Keltner Bot 2.0 is a separate next project.

## Safety status

Agent 05 remains the final deterministic permission authority and fails closed on invalid, stale or unsafe Agent 04 state. Agent 06 remains read-only and explicitly exposes `execution_enabled: false`. Historical, replay and market-data work is evidence-only and does not create trading authority.

## Current Phase 2 milestone

PR #20 merged on 2026-08-01, integrating deterministic per-horizon evidence-coverage missing counts and EMPTY/PARTIAL/COMPLETE status while remaining read-only and fail-closed.

PR #21 — historical XAUUSD ingestion — integrated into `main` at merge commit `66f84839c7d31a50a51ae51c29436675caf617db` after corrected exact-head CI passed (Tests run #206). The implementation reuses the existing Agent02 `IMarketDataProvider` / `TwelveDataProvider` transport rather than duplicating provider integration.

PR #21 adds canonical candle validation, append-only JSONL persistence, deterministic timestamp idempotency, fail-closed rejection of malformed/duplicate persisted history, and injected-provider tests. Empty provider results are a true no-op and do not create storage. It does not write current Agent02 state, Agent04 decisions, Agent05 permission or Agent06 alerts.

PR #22 — deterministic historical replay — integrated into `main` at merge commit `885e51948ea8377d7896913a2519da7fc5e45ebe` after exact-head CI run #213 passed. The replay layer is transport-free and evidence-only over the validated append-only candle contract.

PR #22 adds `market/replay.py`: it validates the complete persisted candle dataset before invoking any callback, requires strict chronological ordering and unique timestamps, and replays candles exactly once with deterministic zero-based sequence numbers. Malformed, duplicate or out-of-order history fails before callbacks receive any candle. Replay does not invoke Agent04/05/06, perform networking, write current state or create execution authority.

PR #23 — versioned deterministic feature extraction — integrated into `main` at merge commit `1e18dc7199c2ae14d70a6d2024374adff5ab58ed` after exact-head CI run #221 passed. The transform consumes validated chronological historical candles, reuses Agent02's existing indicator implementations, emits per-candle evidence records with explicit schema/transform versions and warm-up readiness, and has deterministic tests for reproducibility and fail-closed input validation.

## Contract snapshot

Agent 02 → Agent 04:
- health SUCCESS or DEGRADED;
- valid `generated_at` ≤20 minutes old;
- usable timeframe has non-null `ema20`, `ema50`, `rsi`, `adx`, `trend`.

Agent 03 → Agent 04:
- health SUCCESS or DEGRADED;
- valid `generated_at` ≤6 hours old;
- `gold_bias` + `news_risk`;
- RSS risk LOW/MEDIUM/HIGH only.

Agent 04 → Agent 05:
- valid normalized decision state ≤15 minutes old;
- failed/stale/invalid means BLOCK_TRADING downstream;
- degraded means CAUTION downstream;
- alignment/conflict metadata is intelligence only and does not increase authority.

Agent 05 → Agent 06:
- valid normalized permission state ≤15 minutes old;
- known permissions only: ALLOW_BUYS, ALLOW_SELLS, ALLOW_BOTH, CAUTION, BLOCK_TRADING;
- invalid/stale/unknown fails to BLOCK_TRADING;
- degraded authority cannot pass through as ALLOW_*.

Agent 06 → Trader View → historical evidence:
- Agent 06 remains the permission authority and is informational/read-only;
- Trader View must explicitly identify `mode: READ_ONLY`, `symbol: XAUUSD`, and `execution_enabled: false` before becoming a prediction snapshot;
- historical evidence rejects execution-bearing inputs and preserves immutable predictions with separately appended outcomes;
- analytics and replay are read-only and cannot increase trading authority.

Historical market-data ingestion:
- uses the existing `IMarketDataProvider` / `TwelveDataProvider` path rather than duplicating transport;
- canonical candles require timezone-aware ISO-8601 `datetime` plus finite positive OHLC values with OHLC consistency;
- historical persistence is append-only JSONL and keyed idempotently by candle timestamp;
- existing malformed or duplicate persisted history fails closed before any append;
- empty provider results are a true no-op and do not create empty history files;
- ingestion is evidence-only and never writes current Agent02 state, Agent04 decisions, Agent05 permission or Agent06 alerts.

Replay contract:
- validates the entire persisted candle file before any callback is invoked;
- requires unique, strictly increasing normalized timestamps;
- missing history is an empty replay and does not create storage;
- replay emits deterministic zero-based sequence numbers and copied candle records;
- replay performs no networking, scheduling, current-state writes, permission evaluation, alert generation or execution.

Feature extraction contract:
- consumes only validated, strictly chronological historical candles;
- reuses Agent02 indicator implementations rather than duplicating technical-indicator formulas;
- emits one immutable evidence record per candle with `schema_version`, `transform_version`, timestamp, technical features and explicit warm-up `ready` state;
- duplicate, out-of-order, malformed or non-finite inputs fail closed before feature output is returned;
- feature extraction performs no networking, scheduling, current-state writes, permission evaluation, alert generation or execution.

## CI / test evidence

- `.github/workflows/tests.yml` runs `python -m unittest discover -s tests -v` on push and pull request using Python 3.11.
- Deterministic V1 and all previously merged Phase 2 milestones through PR #21 have recorded clean CI evidence in the prior project history.
- PR #21 final exact-head CI run #206: **SUCCESS** and PR #21 merged after clean CI, mergeability and zero unresolved review threads.
- PR #22 exact-head CI run #213: **SUCCESS** with deterministic replay tests covering chronological replay, malformed-history preflight rejection, out-of-order rejection, empty replay and callback validation.
- PR #22 merged only after clean exact-head CI, mergeability and zero unresolved review threads.
- PR #23 exact-head CI run #221: **SUCCESS** and PR #23 merged after clean exact-head CI, mergeability and zero unresolved review threads.

## Remaining risks / technical debt

1. Agent 03 lacks a validated scheduled-event calendar, so EXTREME event windows remain intentionally unavailable.
2. Freshness thresholds need later empirical validation against workflow cadence/session behavior.
3. Agent 01 remains monolithic and credential-dependent but isolated.
4. Operational orchestration must not accidentally become autonomous execution.
5. Historical JSONL duplicate checks still scan existing records; indexing should be hardened only when evidence volume justifies it.
6. Twelve Data network collection is isolated behind `TwelveDataProvider`; live collection requires credentialed runtime validation and must remain outside deterministic tests.
7. Outcome timing enforces a minimum horizon but does not impose a maximum lateness/tolerance window; choose that only with collection-cadence evidence.
8. Observation/outcome collection cadence is not yet scheduled.
9. Coverage analytics currently reports evidence completeness only; directional/performance statistics require a trustworthy observation-time reference-price contract.

## Active Phase 2 loop

1. **BLOCKED — collection cadence decision:** outcome lateness tolerance cannot be defined responsibly until the observation/outcome collection cadence is established. GitHub Issue #24 tracks the required decision and keeps the work evidence-only.
2. Once cadence is established, implement and deterministically test the evidence-supported outcome lateness tolerance.
3. Extend analytics with directional/performance statistics only after the observation-time reference-price contract is exercised against representative evidence; analytics failures must never increase authority.
4. Harden historical indexing only when evidence volume justifies it.
