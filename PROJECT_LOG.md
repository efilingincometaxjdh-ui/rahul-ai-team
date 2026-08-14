# Rahul AI Team — Project Log

Last audited: 2026-08-14
Branch: `agent/ctrader-market-data`
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

PR #21 — historical XAUUSD ingestion — integrated into `main` at merge commit `66f84839c7d31a50a51ae51c29436675caf617db` after corrected exact-head CI passed (Tests run #206). The implementation reuses the existing Agent02 provider abstraction rather than duplicating provider integration.

PR #21 adds canonical candle validation, append-only JSONL persistence, deterministic timestamp idempotency, fail-closed rejection of malformed/duplicate persisted history, and injected-provider tests. Empty provider results are a true no-op and do not create storage. It does not write current Agent02 state, Agent04 decisions, Agent05 permission or Agent06 alerts.

PR #22 — deterministic historical replay — integrated into `main` at merge commit `885e51948ea8377d7896913a2519da7fc5e45ebe` after exact-head CI run #213 passed. The replay layer is transport-free and evidence-only over the validated append-only candle contract.

PR #22 adds `market/replay.py`: it validates the complete persisted candle dataset before invoking any callback, requires strict chronological ordering and unique timestamps, and replays candles exactly once with deterministic zero-based sequence numbers. Malformed, duplicate or out-of-order history fails before callbacks receive any candle. Replay does not invoke Agent04/05/06, perform networking, write current state or create execution authority.

PR #23 — versioned deterministic feature extraction — integrated into `main` at merge commit `1e18dc7199c2ae14d70a6d2024374adff5ab58ed` after exact-head CI run #221 passed. The transform consumes validated chronological historical candles, reuses Agent02's existing indicator implementations, emits per-candle evidence records with explicit schema/transform versions and warm-up readiness, and has deterministic tests for reproducibility and fail-closed input validation.

**2026-08-08 cadence decision:** Phase 2 observation snapshots are to be collected on a **15-minute cadence**, because 15m is the shortest existing outcome horizon and the Phase 2 plan requires outcomes at +15m, +1h and +4h. A single 15-minute scheduler cadence can therefore create observations and service all three due horizons without introducing a faster-than-required collection loop. This decision defines collection frequency only; it does **not** define an outcome lateness tolerance. Lateness tolerance remains evidence-dependent and will be derived from measured scheduler/reference-feed behavior rather than assumed.

**2026-08-08 scheduler milestone:** Implemented a deterministic, transport-free 15-minute scheduling boundary in `history/scheduler.py` with UTC quarter-hour slot normalization, idempotent slot-due detection, minimum-horizon due checks for +15m/+1h/+4h, and next-slot calculation. Added deterministic tests covering timezone normalization, slot boundaries, due horizons, next-slot behavior and fail-closed rejection of naive timestamps. This work does not perform scheduling, networking, persistence, permission evaluation, alert generation or execution; it is the timing contract only.

**2026-08-08 scheduler integration:** PR #25 merged into `main` at commit `411eafa472f414de571c5faf48d590aed50f28b4` after exact-head CI run #230 passed; no lateness tolerance or live scheduler/reference-feed behavior has been inferred from CI.

**2026-08-10 cTrader migration:** PR #27 replaces the active Twelve Data runtime with Spotware's cTrader Open API and adds supplemental read-only Binance crypto telemetry. XAUUSD remains cTrader-broker sourced; Binance is not used as an XAUUSD substitute.

**2026-08-14 cTrader scaling integrity fix:** Reviewed the cTrader trendbar normalization and found a hard-coded `100000` price divisor despite the provider already resolving the broker symbol's `digits`. Corrected normalization to derive the scale as `10 ** digits`, added deterministic tests for non-default precision and invalid digits, and kept the change strictly inside the market-data evidence boundary. This prevents silently corrupted XAUUSD prices when the broker symbol precision differs from the assumed scale.

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
- uses the provider abstraction and is evidence-only;
- canonical candles require timezone-aware ISO-8601 `datetime` plus finite positive OHLC values with OHLC consistency;
- historical persistence is append-only JSONL and keyed idempotently by candle timestamp;
- existing malformed or duplicate persisted history fails closed before any append;
- empty provider results are a true no-op and do not create empty history files;
- ingestion is evidence-only and never writes current Agent02 state, Agent04 decisions, Agent05 permission or Agent06 alerts.

cTrader provider contract:
- XAUUSD is broker-sourced through cTrader Open API only;
- required runtime secrets are `CTRADER_CLIENT_ID`, `CTRADER_CLIENT_SECRET`, and `CTRADER_ACCESS_TOKEN`; account ID is optional and must be granted to the token when supplied;
- broker symbol identity is discovered dynamically and normalized case-insensitively;
- trendbar prices are scaled from the resolved symbol `digits` value, never from a hard-coded divisor;
- deterministic tests remain network-free;
- runtime collection remains market-data-only and cannot grant Agent04/05/06 authority.

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

Observation/outcome scheduler boundary:
- UTC-aware timestamps are normalized into 15-minute observation slots;
- a snapshot is due when no prior observation exists or the current 15-minute slot is newer than the last observed slot;
- outcome horizons become due only at their minimum elapsed time: +15m, +1h and +4h;
- the scheduler boundary does not define maximum lateness/tolerance and does not acquire reference prices;
- scheduler helpers are deterministic, transport-free and evidence-only.

## CI / test evidence

- `.github/workflows/tests.yml` runs `python -m unittest discover -s tests -v` on push and pull request using Python 3.11.
- Deterministic V1 and previously merged Phase 2 milestones through PR #25 have recorded clean CI evidence.
- PR #21 final exact-head CI run #206: **SUCCESS**.
- PR #22 exact-head CI run #213: **SUCCESS**.
- PR #23 exact-head CI run #221: **SUCCESS**.
- PR #25 exact-head CI run #230: **SUCCESS**.
- PR #27 pre-hardening exact-head CI passed, but the branch has changed since then; fresh exact-head CI is required after the scaling fix.
- Current PR #27 head `ba296471a82b92a732935f8ee09e01fb8106937c` has no completed workflow result yet.

## Remaining risks / technical debt

1. Agent 03 lacks a validated scheduled-event calendar, so EXTREME event windows remain intentionally unavailable.
2. Freshness thresholds need later empirical validation against workflow cadence/session behavior.
3. Agent 01 remains monolithic and credential-dependent but isolated.
4. Operational orchestration must not accidentally become autonomous execution.
5. Historical JSONL duplicate checks still scan existing records; indexing should be hardened only when evidence volume justifies it.
6. cTrader runtime requires a valid access token and credentialed demo validation; deterministic tests must remain network-free.
7. Outcome timing enforces a minimum horizon but does not impose a maximum lateness/tolerance window; choose that only with collection-cadence evidence.
8. Observation/outcome collection cadence is now defined as 15 minutes; the deterministic timing boundary is implemented, while real scheduler/reference-feed lateness measurement remains unfinished.
9. Coverage analytics currently reports evidence completeness only; directional/performance statistics require a trustworthy observation-time reference-price contract exercised against representative evidence.
10. Representative timing evidence remains unfinished until the cTrader runtime produces real timestamped observations.
11. PR #27 is currently non-mergeable and requires fresh exact-head CI plus credentialed demo runtime validation before integration.

## Active Phase 2 loop

1. **Cadence decision complete:** observations are intended to be collected every 15 minutes; this is sufficient to service the existing +15m, +1h and +4h outcome horizons. No lateness tolerance is assumed.
2. **Scheduler boundary complete:** deterministic 15-minute observation/outcome timing helpers are integrated and covered by exact-head CI run #230.
3. **Provider decision approved:** cTrader is now the intended primary XAUUSD market-data source; PR #27 remains subject to technical validation and mergeability.
4. **Current gate:** fresh exact-head CI for PR #27 after the scaling-integrity fix, followed by resolving the branch's mergeability state.
5. **Runtime gate:** configure cTrader demo credentials, run Agent 02, verify M5/M15/H1/H4 XAUUSD artifacts and repeated timestamped observations.
6. After representative timing evidence exists, derive and enforce outcome lateness tolerance.
7. Extend analytics with directional/performance statistics only after the observation-time reference-price contract is exercised against representative evidence; analytics failures must never increase authority.
8. Harden historical indexing only when evidence volume justifies it.
