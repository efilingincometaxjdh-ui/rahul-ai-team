# Rahul AI Team

Rahul AI Team is modular XAUUSD intelligence infrastructure built around deterministic, fail-closed contracts. It is **not an autonomous trading system**.

## Deterministic V1 architecture

```text
Agent 02 — Technical Intelligence ─┐
                                  ├→ Agent 04 — Decision Engine
Agent 03 — Macro/News Intelligence┘
                                         ↓
                              Agent 05 — Permission Engine
                                         ↓
                              Agent 06 — Alert Gateway
                                  (read-only / no execution)
```

Agent 01 is intentionally isolated from V1 because its LLM macro analysis overlaps Agent 03 and its legacy bot-action path conflicts with the intelligence → decision → permission separation. It is preserved for later research, not silently double-counted.

## Agent 02 — XAUUSD Technical Intelligence

Requests M5, M15, H1 and H4 candles from Twelve Data and calculates EMA20, EMA50, RSI14, ATR14, ADX14 and market structure. It writes normalized state to `data/current/agent02.json`.

Health values are `SUCCESS`, `DEGRADED`, or `FAILED`. Agent 04 accepts only structurally usable technical timeframes and requires Agent 02 state to be no more than 20 minutes old.

Configuration: `TWELVE_DATA_API_KEY` must be supplied as an environment variable / GitHub Actions secret. Never commit credentials.

## Agent 03 — XAUUSD Macro/News Intelligence

Uses official Federal Reserve RSS sources and deterministic gold-impact headline scoring. It writes `data/current/agent03.json` with `gold_bias`, score, confidence and explicit observed-headline `news_risk`.

RSS risk is `LOW`, `MEDIUM`, or `HIGH`. Agent 03 deliberately does not infer `EXTREME` from keyword counts; that classification is reserved for a future validated event-calendar source. Agent 04 requires Agent 03 state to be no more than six hours old.

## Agent 04 — Decision Engine

Fuses Agent 02 and Agent 03 state. Technical timeframes are weighted H4=4, H1=3, M15=2, M5=1. Trend uses weighted voting while EMA20, EMA50, RSI and ADX use weighted averages.

Missing, malformed, failed, stale or future-dated required intelligence fails closed to `NO_TRADE`, confidence 0 and failed health. A degraded upstream state remains degraded downstream.

Output: `data/current/decision.json`.

## Agent 05 — Permission Engine

The final deterministic safety gate. It maps valid decisions to `ALLOW_BUYS`, `ALLOW_SELLS`, `ALLOW_BOTH`, `CAUTION`, or `BLOCK_TRADING`.

It fails closed on invalid input, unknown decision/risk states, invalid confidence, `NO_TRADE`, `EXTREME` risk and stale Agent 04 state. A degraded Agent 04 state can produce only `CAUTION`, never trading authority. Agent 04 decisions may be at most 15 minutes old.

Output: `data/current/permission.json`.

## Agent 06 — Alert Gateway

Agent 06 is a read-only downstream boundary. It consumes Agent 05 state and emits an alert/status state containing permission, reason, upstream health and freshness. It **does not place, modify or close trades and contains no broker integration**.

## State contract

Normalized state files are written atomically through `utils/json_writer.py` and include `agent`, `version`, UTC `generated_at`, `status`, and `data`, with optional `errors` and `metadata`.

Freshness is a safety contract, not presentation metadata. Stale or invalid timestamps reduce authority and can never create permission.

## Run locally

```bash
python agent02.py
python agent03.py
python agent04.py
python agent05.py
python agent06.py
```

Agent 02 requires its API key. Agent 03 requires network access to its official RSS sources. Agents 04–06 consume normalized local state.

## Tests

```bash
python -m unittest discover -s tests -v
```

The `Tests` GitHub Actions workflow runs on pushes and pull requests. Tests cover deterministic scoring, health/degradation behavior, multi-timeframe fusion, fail-closed permissions, freshness gates and synthetic pipeline contracts.

## Automation and safety

Existing intelligence workflows support scheduled/manual collection. Rapidly changing generated market state should be inspected as workflow output/artifacts rather than treated as source code.

No broker/execution adapter belongs in deterministic V1. The roadmap after V1 stability is automation → historical state/outcome collection → architecture hardening → validated integrations → ML-assisted intelligence/feedback → V2. ML should augment rather than blindly replace deterministic safety gates.
