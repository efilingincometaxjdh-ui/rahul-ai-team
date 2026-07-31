# Rahul AI Team — Project Log

Last audited: 2026-07-31
Branch: `main` + draft Phase 2 observation-orchestration work
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
Status: INTEGRATED v0.4.

Multi-timeframe fusion weights H4=4, H1=3, M15=2, M5=1. Agent 02 max age 20 minutes; Agent 03 max age 6 hours. Invalid/stale intelligence fails to `NO_TRADE`, confidence 0, EXTREME risk and FAILED health. Phase 2 metadata explicitly exposes ALIGNED / CONFLICT / NEUTRAL state plus H4/H1, M15/M5 and higher-vs-lower conflict without changing weighted decision authority.

### Agent 05 — Permission Engine
Status: INTEGRATED v0.2.

Final deterministic safety gate. Agent 04 max age 15 minutes. Invalid, failed, unknown, stale or unsafe decision state fails closed. Degraded state produces CAUTION only.

### Agent 06 — Alert Gateway
Status: INTEGRATED v0.1.

Read-only downstream boundary consuming `permission.json`. Agent 05 state max age 15 minutes. Missing/malformed/failed/stale/future-dated/unknown permission state emits `BLOCK_TRADING` and FAILED health. Degraded upstream authority is downgraded to CAUTION. Every alert explicitly contains `execution_enabled: false`. There is no broker library, order placement, trade modification or trade-closing path.

### Trader View
Status: INTEGRATED v0.2.

Trader View exposes Agent04 `ALIGNED / CONFLICT / NEUTRAL`, per-timeframe trends, higher-timeframe conflict, lower-timeframe conflict and higher-vs-lower conflict directly to the trader-readable read-only view. Legacy ratio-derived conflict severity remains for compatibility. Unknown alignment metadata degrades to NEUTRAL intelligence and never changes Agent05/06 permission authority. Execution remains disabled.

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
- Outcome-integrity HEAD `7289267b`: Tests #93 SUCCESS; PR #7 merged.
- Trader View boundary HEAD `893fd357`: Tests #100 SUCCESS; PR #8 merged.
- Outcome-timing HEAD `726dcdbc`: Tests #107 SUCCESS; PR #9 merged.
- Agent04 MTF intelligence HEAD `78ade145`: Tests #112 SUCCESS; PR #10 merged after clean exact-HEAD CI, mergeability check and zero unresolved review threads.
- Trader View MTF presentation HEAD `7e242bbd`: Tests #119 SUCCESS; PR #11 merged after exact-HEAD CI success, mergeability check and zero unresolved review threads.
- Historical MTF evidence HEAD `7720bc5b`: Tests #127 SUCCESS; PR #12 merged after exact-HEAD CI success, mergeability check and zero unresolved review threads.
- Safe observation orchestration: collector + deterministic boundary tests committed on `phase2/safe-observation-orchestration`; exact-HEAD CI pending. Do not integrate before clean evidence.

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
- Trader View v0.2 presents Agent04 alignment/conflict intelligence without modifying permission;
- historical observation rejects unknown decisions/permissions/risks/conflict states, invalid confidence/freshness, execution authority, stale ALLOW states, and decision/permission mismatches;
- prediction snapshots persist validated `timeframe_alignment`, `timeframe_trends`, and higher/lower/cross-group conflict fields while preserving schema v1 compatibility; legacy Trader View inputs receive conservative NEUTRAL/empty/false evidence defaults;
- blocked/NO_TRADE snapshots remain valid evidence when safely blocked.
- proposed observation collector accepts only normalized TraderView envelopes with SUCCESS/DEGRADED health, delegates all data safety checks to the existing observation contract, and only appends evidence; FAILED/unknown/malformed envelopes are rejected and cannot affect current trading state.

## Phase 2 historical evidence — ACTIVE

PR #6 introduced immutable prediction snapshots, deterministic observation IDs, append-only JSONL storage, separate outcomes and explicit `15m`, `1h`, `4h` horizons.

PR #7 hardened outcome integrity with one outcome per `(observation_id, horizon)`, orphan rejection, timezone-aware timestamp/schema validation, finite positive-price validation and fail-closed corrupt-history behavior.

PR #8 requires historical predictions to originate from a valid read-only XAUUSD Trader View and rejects unsafe execution-bearing or contradictory inputs.

PR #9 joins every appended outcome to exactly one source observation and enforces `measured_at >= observed_at + horizon`. Source history is mandatory, duplicate source IDs fail closed, malformed source timestamps/schema fail closed, and timezone-offset comparisons use aware datetime arithmetic.

PR #10 adds explicit Agent04 multi-timeframe alignment/conflict intelligence while preserving deterministic weighted fusion and downstream safety authority.

PR #11 carries that intelligence into Trader View while retaining the Agent06 permission boundary and `execution_enabled: false` invariant.

PR #12 carries explicit MTF intelligence into immutable historical prediction snapshots, validates malformed metadata fail-closed, and preserves compatibility with existing schema-v1 history. Integrated after Tests #127 passed on exact HEAD `7720bc5b`.

Current proposed work adds an explicit evidence-only collector from the normalized `trader_view.json` envelope into append-only observations. It does not schedule itself, invoke upstream agents, write permission/current state, fetch prices, or execute trades.

This layer still does **not** choose a live market-price provider, run continuous collection, calculate performance statistics, or create trading authority.

## Remaining risks / technical debt

1. Agent 03 lacks a validated scheduled-event calendar, so EXTREME event windows remain intentionally unavailable.
2. Freshness thresholds need later empirical validation against workflow cadence/session behavior.
3. Agent 01 remains monolithic and credential-dependent but isolated.
4. Operational orchestration must not accidentally become autonomous execution.
5. Historical JSONL duplicate checks still scan existing records; adequate initially, but indexing should be hardened before large datasets.
6. No validated live reference-price source has been selected for outcome measurement.
7. Outcome timing enforces a minimum horizon but does not impose a maximum lateness/tolerance window; choose that only with collection-cadence evidence.
8. Observation collection cadence is not yet scheduled; cadence should be chosen only after this collector has clean CI and the evidence-volume/freshness implications are reviewed.

## Active Phase 2 loop

1. Obtain exact-HEAD CI for safe observation orchestration; diagnose/fix failures and integrate only if clean and routine.
2. Select/validate a zero-cost reference-price source before measuring +15m/+1h/+4h outcomes.
3. Define evidence-supported outcome lateness tolerance once collection cadence is known.
4. Build performance analytics only after enough trustworthy observations/outcomes exist; analytics failures must never increase authority.
5. Harden historical indexing only when evidence volume justifies it.
