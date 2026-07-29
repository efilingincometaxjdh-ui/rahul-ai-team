# Rahul AI Team — Project Log

Last audited: 2026-07-30
Branch: `agent/recover-agent04-agent05`
PR: #5 (draft; do not merge until latest CI is green)

This file is the source of truth for architecture, recovery evidence, current health, and next work. Update it with every meaningful build loop.

## Loop Engineering protocol

Every build loop follows: **Inspect → Plan → Build → Test → Observe → Critique → Fix → Retest → Integrate → Monitor → Repeat**.

Rules:
- Repository evidence beats assumptions.
- Deterministic safety gates beat model opinions.
- Generated state must use the normalized `utils/json_writer.py` envelope.
- Missing, malformed, failed, stale, future-dated, or degraded upstream state must reduce authority, never increase it.
- No execution/broker integration until intelligence and permission layers are independently tested.
- Agent 05 fails closed on `NO_TRADE`, invalid input, unknown decision/risk states, invalid confidence, EXTREME risk, and stale Agent 04 state.

## Architecture

`Agent 02 technical state` + `Agent 03 macro/news state` → **Agent 04 Decision Engine** → **Agent 05 Permission Engine** → future non-executing alert adapter.

Agent 01 remains isolated from this path. Keltner Bot 2.0 is a separate future project.

## Agent status

### Agent 01 — Legacy LLM Macro Analyst
Status: ISOLATED / LEGACY / ACTIVE CODE.

Audit evidence: Agent 01 v3.0 overlaps Federal Reserve collection and directional macro analysis with Agent 03, depends on Gemini, and also produces a bot action through its own RiskEngine. That conflicts with the recovered separation of intelligence → decision → permission.

Resolution: **do not integrate Agent 01 into deterministic V1.** Preserve it as experimental evidence for a later LLM/ML-assisted intelligence layer. Future extraction candidates are article-content enrichment, richer USD analysis, invalidation text, and prediction/outcome recording.

### Agent 02 — XAUUSD Technical Intelligence
Status: BUILT.

Produces normalized M5/M15/H1/H4 technical state with EMA20, EMA50, RSI14, ATR14, ADX14 and market structure.

### Agent 03 — XAUUSD Macro/News Intelligence
Status: BUILT v0.2 / PRIMARY MACRO SOURCE FOR V1; latest CI pending.

Agent 03 now exposes an explicit `news_risk` contract based on observed RSS headlines: LOW when no high-impact headlines are observed, MEDIUM for 1–2, HIGH for 3+. It deliberately **never invents EXTREME from RSS keyword counts**. EXTREME is reserved for a future validated event-calendar source. This prevents headline matching from masquerading as scheduled-event certainty.

### Agent 04 — Decision Engine
Status: RECOVERED + INTEGRATED v0.3; latest CI pending.

Technical fusion consumes every complete timeframe with H4=4, H1=3, M15=2, M5=1. Trend is a weighted vote; EMA20, EMA50, RSI and ADX are weighted averages.

Freshness gate added: Agent 02 technical state may be at most 20 minutes old; Agent 03 macro state may be at most 6 hours old. Missing/invalid `generated_at`, unexpectedly future-dated state, or stale state produces `NO_TRADE`, confidence 0, EXTREME risk and FAILED health. Freshness evidence is recorded in Agent 04 metadata.

### Agent 05 — Permission Engine
Status: RECOVERED + INTEGRATED v0.2; latest CI pending.

Final deterministic safety gate. Agent 04 decision state may be at most 15 minutes old. Missing/malformed/failed/unknown-health/stale/future-dated decision state produces `BLOCK_TRADING` and FAILED health. Valid but degraded Agent 04 state produces CAUTION and no trading authority. Unknown decision/risk states, invalid confidence, `NO_TRADE`, and EXTREME risk also fail closed.

## CI / test evidence

- `.github/workflows/tests.yml` runs `python -m unittest discover -s tests -v` on pushes and pull requests using Python 3.11.
- Original recovery HEAD `bdb0e7e`: Tests run #43 SUCCESS.
- Multi-timeframe/fail-closed HEAD `1f988e98`: Tests run #53 SUCCESS, including the unit-test step.
- The current loop then added freshness enforcement, Agent 03 explicit risk semantics, and synthetic pipeline contract tests. **These newest commits require a fresh green CI run before PR #5 can leave draft or merge.**

## Contract snapshot

Agent 02 → Agent 04:
- status SUCCESS or DEGRADED;
- valid normalized `generated_at` no older than 20 minutes;
- `data` may contain M5/M15/H1/H4;
- usable timeframe requires non-null `ema20`, `ema50`, `rsi`, `adx`, `trend`.

Agent 03 → Agent 04:
- status SUCCESS or DEGRADED;
- valid normalized `generated_at` no older than 6 hours;
- required `data.gold_bias` and `data.news_risk`;
- RSS risk values are LOW/MEDIUM/HIGH only; EXTREME requires future validated event-calendar evidence.

Agent 04 → Agent 05:
- normalized envelope with `generated_at`, `data.decision`, `data.confidence`, `data.risk`, `data.reasons`;
- decision state no older than 15 minutes;
- FAILED/stale/invalid upstream means BLOCK_TRADING;
- DEGRADED upstream means CAUTION.

Agent 05 downstream contract:
- `ALLOW_BUYS`, `ALLOW_SELLS`, `ALLOW_BOTH` require valid, fresh, non-degraded known state with sufficient confidence;
- `CAUTION` carries no autonomous trading authority;
- `BLOCK_TRADING` is fail-closed.

## Deterministic test coverage added this loop

- stale Agent 02 → Agent 04 NO_TRADE/FAILED;
- stale Agent 03 → Agent 04 NO_TRADE/FAILED;
- stale Agent 04 → Agent 05 BLOCK_TRADING/FAILED;
- fresh bullish synthetic pipeline → ALLOW_BUYS;
- degraded synthetic pipeline → CAUTION, never authority;
- Agent 03 LOW/MEDIUM/HIGH risk classification;
- Agent 03 RSS classifier cannot emit EXTREME.

## Current risks / technical debt

1. Newest freshness/risk/contract changes require fresh CI evidence.
2. Agent 03 cannot know scheduled EXTREME event windows without a validated event-calendar source; do not fake this from RSS.
3. Freshness thresholds are deterministic V1 policy and should later be validated against actual workflow cadence and market-session behavior.
4. Agent 01 remains monolithic and credential-dependent; keep isolated.
5. README is behind the architecture.
6. No broker/execution adapter exists by design; do not add autonomous execution.

## Active loop / next actions

1. Observe current PR #5 CI; diagnose/fix/retest any failure.
2. When green, update README to the stable deterministic V1 contracts.
3. Add a read-only/non-executing Agent 06 Alert Gateway that consumes Agent 05 and exposes permission, reason, health and freshness only.
4. Add deterministic Agent 06 tests, including stale/malformed permission-state handling.
5. Re-run CI and update this log.
6. Keep PR #5 draft until the complete recovered V1 scope is green and reviewed for architecture drift.
7. After deterministic V1: automation → historical state/outcome collection → architecture hardening → validated integrations → ML-assisted intelligence/feedback → V2.
