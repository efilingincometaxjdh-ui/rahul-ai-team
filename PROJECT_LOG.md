# Rahul AI Team — Project Log

Last audited: 2026-07-30
Branch: `agent/recover-agent04-agent05`
PR: #5 (draft; do not merge until newest Agent 06 HEAD has clean CI)

This file is the persistent source of truth for architecture, recovery evidence, current health, contracts, safety policy and next work.

## Loop Engineering protocol

**Inspect → Plan → Build → Test → Observe → Critique → Fix → Retest → Integrate → Monitor → Repeat**.

Rules:
- Repository evidence beats assumptions.
- Deterministic safety gates beat model opinions.
- Generated state uses the normalized atomic `utils/json_writer.py` envelope.
- Missing, malformed, failed, stale, future-dated or degraded upstream state reduces authority, never increases it.
- No autonomous execution/broker integration in deterministic V1.
- Agent 05 fails closed on `NO_TRADE`, invalid input, unknown decision/risk states, invalid confidence, EXTREME risk and stale Agent 04 state.
- Agent 06 is read-only and always exposes `execution_enabled: false`.

## Architecture

`Agent 02 Technical` + `Agent 03 Macro/News` → **Agent 04 Decision** → **Agent 05 Permission** → **Agent 06 Alert Gateway (read-only)**.

Agent 01 remains isolated. Keltner Bot 2.0 is a separate next project.

## Agent status

### Agent 01 — Legacy LLM Macro Analyst
Status: ISOLATED / LEGACY.

It overlaps Agent 03 Fed collection/directional analysis, depends on Gemini, and contains a legacy bot-action path that conflicts with intelligence → decision → permission separation. Do not integrate into V1. Preserve for later LLM/ML-assisted research; potential reusable concepts include article enrichment, USD analysis, invalidation text and prediction/outcome recording.

### Agent 02 — XAUUSD Technical Intelligence
Status: BUILT.

Produces normalized M5/M15/H1/H4 state with EMA20, EMA50, RSI14, ATR14, ADX14 and structure.

### Agent 03 — XAUUSD Macro/News Intelligence
Status: BUILT v0.2; GREEN at prior HEAD, newest full-scope CI pending.

Explicit observed-headline `news_risk`: LOW with no high-impact headlines, MEDIUM for 1–2, HIGH for 3+. RSS scoring cannot emit EXTREME; future validated event-calendar evidence is required for EXTREME.

### Agent 04 — Decision Engine
Status: RECOVERED + INTEGRATED v0.3; GREEN at prior HEAD, newest full-scope CI pending.

Multi-timeframe fusion weights H4=4, H1=3, M15=2, M5=1. Agent 02 max age 20 minutes; Agent 03 max age 6 hours. Invalid/stale intelligence fails to `NO_TRADE`, confidence 0, EXTREME risk and FAILED health.

### Agent 05 — Permission Engine
Status: RECOVERED + INTEGRATED v0.2; GREEN at prior HEAD, newest full-scope CI pending.

Final deterministic safety gate. Agent 04 max age 15 minutes. Invalid, failed, unknown, stale or unsafe decision state fails closed. Degraded state produces CAUTION only.

### Agent 06 — Alert Gateway
Status: BUILT v0.1; CI PENDING.

Read-only downstream boundary consuming `permission.json`. Agent 05 state max age 15 minutes. Missing/malformed/failed/stale/future-dated/unknown permission state emits `BLOCK_TRADING` and FAILED health. Degraded upstream authority is downgraded to CAUTION. Every alert explicitly contains `execution_enabled: false`. Output is `data/current/alert.json`. There is no broker library, order placement, trade modification or trade-closing path.

## CI / test evidence

- `.github/workflows/tests.yml` runs `python -m unittest discover -s tests -v` on push and pull request using Python 3.11.
- Recovery HEAD `bdb0e7e`: Tests #43 SUCCESS.
- Multi-timeframe/fail-closed HEAD `1f988e98`: Tests #53 SUCCESS.
- Freshness/risk/end-to-end HEAD `06d79b5d`: Tests #67 SUCCESS including unit tests.
- README + Agent 06 + Agent 06 tests were added after #67. The newest Agent 06 test commit `14c7da8a` had no PR workflow run visible at the first observation. **Do not merge until a workflow for the newest effective HEAD completes successfully.**

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

Agent 06 downstream:
- informational alert only;
- always `execution_enabled: false`;
- no autonomous execution capability.

## Deterministic test coverage

Coverage includes scoring, indicator/market health, multi-timeframe conflicts, incomplete timeframes, missing inputs, degraded states, stale Agent 02/03/04 states, invalid permission states, synthetic bullish pipeline, degraded pipeline, Agent 03 risk semantics, and Agent 06 fresh/stale/malformed/unknown/degraded/read-only behavior.

## Documentation

README has been rewritten to document the deterministic V1 architecture, state/freshness contracts, Agent 01 isolation, Agent 06 read-only boundary, local commands, testing and post-V1 roadmap.

## Remaining V1 risks / technical debt

1. New Agent 06 HEAD needs clean CI evidence.
2. Agent 03 lacks a validated scheduled-event calendar, so EXTREME event windows are intentionally unavailable.
3. Freshness thresholds are deterministic V1 policy and need later empirical validation against workflow cadence/session behavior.
4. Agent 01 remains monolithic and credential-dependent but isolated.
5. Operational orchestration of Agent 02→03→04→05→06 is not yet a single autonomous trade system and must not become one accidentally.

## Active loop / finish criteria for PR #5

1. Observe newest CI; fix/retest any failure without bypassing tests.
2. Inspect complete PR #5 diff for architecture drift, execution capability, unsafe fallbacks and documentation mismatch.
3. Verify no unresolved review threads/requested changes.
4. If clean, mark PR #5 ready for review; merge only when evidence remains green and merge state is safe.
5. After merge, verify `main` and update project source of truth if a follow-up documentation commit is needed.
6. Deterministic V1 then moves to post-V1 roadmap: automation/orchestration → historical state/outcome collection → architecture hardening → validated integrations → ML-assisted intelligence/feedback → V2.
