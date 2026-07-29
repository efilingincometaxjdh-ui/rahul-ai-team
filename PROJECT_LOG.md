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
- Missing, malformed, failed, or degraded upstream state must reduce authority, never increase it.
- No execution/broker integration until intelligence and permission layers are independently tested.
- Agent 05 fails closed on `NO_TRADE`, invalid input, unknown decision/risk states, invalid confidence, and EXTREME risk.

## Architecture

`Agent 02 technical state` + `Agent 03 macro/news state` → **Agent 04 Decision Engine** → **Agent 05 Permission Engine** → future alert/execution adapter.

Agent 01 remains isolated from this path. Keltner Bot 2.0 is a separate future project.

## Agent status

### Agent 01 — Legacy LLM Macro Analyst
Status: ISOLATED / LEGACY / ACTIVE CODE.

Audit evidence: Agent 01 v3.0 collects the same Federal Reserve monetary-policy, speech and press-release feeds used by the macro domain, fetches article bodies, sends supplied information to Gemini, produces gold/USD bias, scores, news risk and confidence, then runs its own deterministic `RiskEngine` to produce `bot_action` and records predictions. It requires `GEMINI_API_KEY` at import time and performs network/LLM work at module import.

Overlap resolution decision: **do not integrate Agent 01 into Agent 04 V1.** Agent 03 is the deterministic primary macro/news source. Agent 01 duplicates source collection and directional macro analysis and additionally produces a bot action, which conflicts with the recovered separation of intelligence → decision → permission. Preserve Agent 01 as experimental/legacy evidence for a later ML/LLM-assisted intelligence layer. Do not delete it yet.

Future extraction candidates from Agent 01: article-content enrichment, richer USD analysis, invalidation text, prediction/outcome recording. These may be migrated into separate components only after deterministic V1 stabilizes.

### Agent 02 — XAUUSD Technical Intelligence
Status: BUILT.

Evidence: fetches M5/M15/H1/H4 XAUUSD candles from Twelve Data and calculates EMA20, EMA50, RSI14, ATR14, ADX14 and market structure. It writes normalized `agent02.json`. Unit tests cover indicators, structure, partial-data degradation, total failure and state I/O.

### Agent 03 — XAUUSD Macro/News Intelligence
Status: BUILT v0.1 / PRIMARY MACRO SOURCE FOR V1.

Evidence: uses official Federal Reserve RSS plus deterministic headline scoring and writes normalized `agent03.json`. It exposes `gold_bias`, `macro_score`, `confidence`, headline count and high-impact count. Current limitation: it does not yet expose an explicit LOW/MEDIUM/HIGH/EXTREME `news_risk` contract; Agent 04 conservatively maps any high-impact headline to HIGH rather than inventing EXTREME semantics.

### Agent 04 — Decision Engine
Status: RECOVERED + INTEGRATED v0.2; latest CI pending.

Recovery evidence: `decision/engine.py` and commit history establish the Decision Engine role. It combines macro bias/risk with technical trend, EMA, ADX and RSI.

Current implementation: `agent04.py` reads normalized Agent 02/03 state. Technical fusion now consumes every complete timeframe rather than selecting one. Weights are H4=4, H1=3, M15=2, M5=1. Trend is a weighted vote; EMA20, EMA50, RSI and ADX are weighted averages. Incomplete timeframes are excluded. If no complete timeframe exists, Agent 04 returns `NO_TRADE`, confidence 0, EXTREME risk and FAILED health. Any degraded upstream state makes Agent 04 DEGRADED.

### Agent 05 — Permission Engine
Status: RECOVERED + INTEGRATED; latest CI pending.

Current policy: final deterministic safety gate. It blocks invalid/non-dict input, unknown decision states, unknown risk states, invalid confidence, `NO_TRADE`, and EXTREME risk. Low confidence produces CAUTION. A DEGRADED Agent 04 state can never become trading authority; the runner converts it to CAUTION/human review.

## CI / test evidence

- Repository workflow `.github/workflows/tests.yml` runs `python -m unittest discover -s tests -v` on pushes and pull requests using Python 3.11.
- PR #5 original recovery HEAD `bdb0e7e` completed Tests run #43 successfully; the test job and unit-test step both concluded SUCCESS.
- After that green baseline, the loop changed Agent 04 to multi-timeframe fusion and strengthened Agent 05 unknown-state fail-closed behavior, with corresponding deterministic tests.
- **Latest branch HEAD must receive a fresh successful CI run before PR #5 can leave draft or merge.** No test failure may be bypassed.

## Contract snapshot

Agent 02 → Agent 04:
- envelope status must be SUCCESS or DEGRADED;
- `data` may contain M5/M15/H1/H4;
- a usable timeframe requires non-null `ema20`, `ema50`, `rsi`, `adx`, `trend`.

Agent 03 → Agent 04:
- envelope status must be SUCCESS or DEGRADED;
- required directional input: `data.gold_bias`;
- `data.high_impact_count > 0` currently maps to HIGH news risk; otherwise LOW.

Agent 04 → Agent 05:
- normalized envelope with `data.decision`, `data.confidence`, `data.risk`, `data.reasons`;
- FAILED upstream means no authority;
- DEGRADED upstream means CAUTION at Agent 05.

Agent 05 downstream contract:
- `ALLOW_BUYS`, `ALLOW_SELLS`, `ALLOW_BOTH` are possible only from valid, non-degraded known state with sufficient confidence;
- `CAUTION` carries no autonomous trading authority;
- `BLOCK_TRADING` is the fail-closed state.

## Current risks / technical debt

1. Latest Agent 04/05 changes still require fresh CI evidence.
2. Agent 03 lacks explicit event-risk severity; high-impact detection is not equivalent to an EXTREME event calendar.
3. State freshness/maximum age is not yet enforced by Agent 04/05. A structurally valid but stale state could currently be consumed.
4. Agent 01 remains monolithic, credential-dependent and performs side effects at import; keep isolated.
5. README is behind the recovered architecture.
6. No broker/execution adapter exists by design; do not add autonomous execution yet.

## Active loop / next actions

1. Observe latest PR #5 CI and fix any failure; keep draft until clean.
2. Add deterministic state freshness validation so stale Agent 02/03/04 states fail closed.
3. Add/validate explicit Agent 03 news-risk semantics without conflating a keyword hit with an EXTREME event.
4. Run end-to-end contract tests for Agent02 + Agent03 → Agent04 → Agent05 using synthetic normalized states.
5. Update README after contracts stabilize.
6. Design a **non-executing downstream alert interface** first: consume Agent 05 state, expose permission/reason/health/freshness, and never place trades.
7. Only after deterministic V1 stability: automation → historical state/outcome collection → architecture hardening → validated integrations → ML-assisted intelligence/feedback → V2.
