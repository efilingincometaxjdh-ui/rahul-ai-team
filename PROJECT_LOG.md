# Rahul AI Team — Project Log

Last audited: 2026-07-31
Branch: `phase2-trader-observation-contract`
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

## Deterministic V1 status

PR #5 merged to `main` on 2026-07-30 after clean effective-HEAD CI (Tests #75). Deterministic V1 is integrated.

### Agent 02 — XAUUSD Technical Intelligence
Status: BUILT.

Produces normalized M5/M15/H1/H4 state with EMA20, EMA50, RSI14, ATR14, ADX14 and structure.

### Agent 03 — XAUUSD Macro/News Intelligence
Status: BUILT v0.2.

Explicit observed-headline `news_risk`: LOW with no high-impact headlines, MEDIUM for 1–2, HIGH for 3+. RSS scoring cannot emit EXTREME; future validated event-calendar evidence is required for EXTREME.

### Agent 04 — Decision Engine
Status: INTEGRATED v0.3.

Multi-timeframe fusion weights H4=4, H1=3, M15=2, M5=1. Agent 02 max age 20 minutes; Agent 03 max age 6 hours. Invalid/stale intelligence fails to `NO_TRADE`, confidence 0, EXTREME risk and FAILED health.

### Agent 05 — Permission Engine
Status: INTEGRATED v0.2.

Final deterministic safety gate. Agent 04 max age 15 minutes. Invalid, failed, unknown, stale or unsafe decision state fails closed. Degraded state produces CAUTION only.

### Agent 06 — Alert Gateway
Status: INTEGRATED v0.1.

Read-only downstream boundary consuming `permission.json`. Agent 05 state max age 15 minutes. Missing/malformed/failed/stale/future-dated/unknown permission state emits `BLOCK_TRADING` and FAILED health. Degraded upstream authority is downgraded to CAUTION. Every alert explicitly contains `execution_enabled: false`. There is no broker library, order placement, trade modification or trade-closing path.

### Agent 01 — Legacy LLM Macro Analyst
Status: ISOLATED / LEGACY.

It overlaps Agent 03 and contains a legacy bot-action path that conflicts with intelligence → decision → permission separation. Do not integrate without a deliberate overlap-resolution decision.

## CI / test evidence

- `.github/workflows/tests.yml` runs `python -m unittest discover -s tests -v` on push and pull request using Python 3.11.
- Recovery HEAD `bdb0e7e`: Tests #43 SUCCESS.
- Multi-timeframe/fail-closed HEAD `1f988e98`: Tests #53 SUCCESS.
- Freshness/risk/end-to-end HEAD `06d79b5d`: Tests #67 SUCCESS.
- Deterministic V1 effective HEAD `8501a1d0`: Tests #75 SUCCESS; PR #5 merged.
- Phase 2 historical observation HEAD `27f54dca`: Tests #86 SUCCESS; PR #6 merged.
- Outcome-integrity HEAD `7289267b`: Tests #93 SUCCESS; PR #7 merged after evidence review.
- Trader View observation-boundary branch: implementation/tests added; fresh CI required before integration.

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
- degraded means CAUTION downstream.

Agent 05 → Agent 06:
- valid normalized permission state ≤15 minutes old;
- known permissions only: ALLOW_BUYS, ALLOW_SELLS, ALLOW_BOTH, CAUTION, BLOCK_TRADING;
- invalid/stale/unknown fails to BLOCK_TRADING;
- degraded authority cannot pass through as ALLOW_*.

Agent 06 → Trader View → historical evidence:
- Agent 06 remains the permission authority and is informational/read-only;
- Trader View must explicitly identify `mode: READ_ONLY`, `symbol: XAUUSD`, and `execution_enabled: false` before becoming a prediction snapshot;
- historical observation rejects unknown decisions/permissions/risks/conflict states, invalid confidence/freshness, execution authority, stale ALLOW states, and decision/permission mismatches;
- blocked/NO_TRADE snapshots remain valid evidence when they are safely blocked, so later analytics can measure avoided setups without increasing authority.

## Phase 2 historical evidence — ACTIVE

PR #6 introduced the first append-only observation/outcome contract:
- immutable prediction snapshots with deterministic observation IDs;
- append-only JSONL storage with duplicate-ID idempotency;
- outcomes are separate events and never mutate the prediction snapshot;
- supported horizons are explicitly `15m`, `1h`, `4h`;
- invalid horizons and non-positive prices fail validation.

PR #7 hardened outcome integrity:
- append-only outcome writer without rewriting prediction history;
- one outcome per `(observation_id, horizon)`;
- optional orphan-outcome rejection against observation history;
- timezone-aware ISO-8601 timestamp and schema validation;
- rejection of NaN/infinite/non-positive prices;
- fail-closed behavior when existing JSONL is corrupt or structurally invalid.

Current branch hardens the input boundary so historical predictions can only be constructed from a valid read-only Trader View contract. Unsafe execution-bearing input is rejected rather than silently sanitized.

This layer still does **not** choose a live market-price provider, run continuous collection, calculate performance statistics, or create trading authority.

## Remaining risks / technical debt

1. Agent 03 lacks a validated scheduled-event calendar, so EXTREME event windows remain intentionally unavailable.
2. Freshness thresholds need later empirical validation against workflow cadence/session behavior.
3. Agent 01 remains monolithic and credential-dependent but isolated.
4. Operational orchestration must not accidentally become autonomous execution.
5. Historical JSONL duplicate checks still scan existing records; adequate for initial evidence volume, but indexing should be hardened before large datasets.
6. No validated live reference-price source has been selected for outcome measurement.
7. Outcome timing validates timestamp syntax but does not yet enforce measured-at >= observation time plus the requested horizon; this requires joining observation metadata.

## Active Phase 2 loop

1. Obtain clean CI evidence for Trader View → historical prediction boundary and integrate only if green.
2. Enforce outcome timing integrity against the source observation before operational collection.
3. Improve Agent 04 explicit multi-timeframe alignment/conflict intelligence without weakening Agent 05 safety authority.
4. Add safe observation workflow orchestration only after contracts are green.
5. Select/validate a zero-cost reference-price source before measuring +15m/+1h/+4h outcomes.
6. Build performance analytics only after enough trustworthy observations/outcomes exist; analytics failures must never increase authority.
