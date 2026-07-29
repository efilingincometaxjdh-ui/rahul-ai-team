# Rahul AI Team — Project Log

Last audited: 2026-07-30
Branch: `agent/recover-agent04-agent05`

This file is the source of truth for architecture, recovery evidence, current health, and next work. Update it with every meaningful build loop.

## Loop Engineering protocol

Every build loop follows: **Observe → Recover evidence → Plan smallest safe change → Implement → Test → Inspect outputs/failures → Update this log → Repeat**.

Rules:
- Repository evidence beats assumptions.
- Deterministic safety gates beat model opinions.
- Generated state must use the normalized `utils/json_writer.py` envelope.
- Missing, stale, malformed, or degraded upstream state must reduce authority, never increase it.
- No execution/broker integration until intelligence and permission layers are independently tested.

## Audit snapshot

### Agent 01 — XAUUSD Macro Intelligence
Status: LEGACY / ACTIVE CODE, needs modernization.

Evidence: `agent01.py` is a large Gemini-backed macro analyst using Federal Reserve feeds, article extraction, a deterministic risk engine, and prediction recording. It requires `GEMINI_API_KEY`. It overlaps with Agent 03 and currently performs substantial work at import time, which makes isolated testing harder.

### Agent 02 — XAUUSD Market Intelligence
Status: BUILT.

Evidence: `agent02.py` fetches M5/M15/H1/H4 XAUUSD candles from Twelve Data and calculates EMA20, EMA50, RSI14, ATR14, ADX14 and market structure. It writes normalized `agent02.json` health state. Tests and scheduled GitHub Actions exist.

### Agent 03 — XAUUSD Macro/News Intelligence
Status: BUILT v0.1.

Evidence: `agent03.py`, `macro/rss.py`, `macro/scoring.py`, tests and scheduled workflow exist. It uses official Federal Reserve RSS plus deterministic headline scoring and writes normalized `agent03.json`.

### Agent 04 — Decision Engine
Status: RECOVERED FROM REPOSITORY EVIDENCE; integration incomplete.

Evidence: `decision/engine.py` exists as Decision Engine v1.0. Historical commits show it was intentionally created and populated. It combines macro `gold_bias/news_risk` with technical trend, EMA20/EMA50, ADX and RSI into `STRONG_BULLISH/BULLISH/NEUTRAL/BEARISH/STRONG_BEARISH`, with `NO_TRADE` on EXTREME news risk. `data/current/decision.json` is a placeholder state artifact. There is no current Agent 04 runner, normalized state writer integration, or dedicated tests/workflow.

Recovery decision: Agent 04 is the repository's **Decision Engine**. Preserve the recovered deterministic scoring concept, but harden input validation and wire it to normalized Agent 02/03 state.

### Agent 05 — Permission Engine
Status: RECOVERED FROM REPOSITORY EVIDENCE; integration incomplete.

Evidence: `permissions/engine.py` exists and historical commits show it was intentionally created/populated. It maps decision states to `ALLOW_BUYS/ALLOW_SELLS/ALLOW_BOTH/CAUTION/BLOCK_TRADING`, with an EXTREME-risk hard block. `data/current/permission.json` is a placeholder state artifact. The recovered code reads confidence but does not use it, does not explicitly handle `NO_TRADE`, and has no runner/tests/workflow.

Recovery decision: Agent 05 is the repository's **Permission Engine / final deterministic safety gate**. It must fail closed on bad/degraded inputs and explicitly block `NO_TRADE`.

## Architecture recovered

`Agent 02 technical state` + `Agent 03 macro/news state` → **Agent 04 Decision Engine** → **Agent 05 Permission Engine** → future alert/execution adapter.

Agent 01 is older macro intelligence and is not currently placed in the primary Agent 04 fusion path because Agent 03 is the newer deterministic macro/news component. Agent 01 should later be evaluated as an optional secondary macro source rather than silently double-counted.

## Current risks / technical debt

1. README still describes Agent 02 as the first production component and does not document Agent 03/04/05.
2. Agent 01 and Agent 03 overlap in macro responsibility.
3. Agent 04 recovered engine assumes a single technical dictionary while Agent 02 emits multiple timeframes.
4. Agent 04/05 placeholder JSON files are not trustworthy live state.
5. Agent 05 recovered engine does not use its `confidence` variable and does not explicitly block `NO_TRADE`.
6. No Agent 04/05 tests or automation are present at audit time.
7. CI status must be verified after the recovery branch is built.

## Active loop

Goal: recover Agent 04 and Agent 05 into runnable, tested modules without adding broker execution.

Planned sequence:
1. Harden DecisionEngine while preserving recovered scoring semantics.
2. Add Agent 04 runner to read Agent 02/03 normalized states and fuse multi-timeframe technical evidence.
3. Harden PermissionEngine to fail closed.
4. Add Agent 05 runner.
5. Add deterministic tests for decision/permission behavior and state validation.
6. Add GitHub Actions validation/automation only after tests pass.
7. Update README and this log with observed results.
