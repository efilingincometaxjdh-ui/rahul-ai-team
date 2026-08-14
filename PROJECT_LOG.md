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

## Current cTrader decision

2026-08-14: Product-owner decision received to adopt cTrader as the primary XAUUSD market-data source for Agent 02. PR #27 remains a market-data-only migration; no execution/order/position operations are permitted. cTrader credentials are expected only through GitHub Actions secrets and must never be committed or logged.

## cTrader migration gate

PR #27 replaces the active Twelve Data runtime with Spotware cTrader Open API and adds supplemental read-only Binance crypto telemetry. XAUUSD remains cTrader-broker sourced; Binance is not an XAUUSD substitute.

A deterministic price-scaling defect was found and corrected on the cTrader branch: candle prices must be scaled from the broker symbol's discovered `digits` (`10 ** digits`) rather than a hard-coded divisor. Invalid digit metadata fails closed. Deterministic tests cover non-default precision.

The current merge-conflict resolution must preserve both safety/evidence concerns from main and the cTrader branch: dependency installation, the 15-minute weekday observation cadence, workflow timing capture, and read-only Agent 02 execution. Fresh exact-head CI is required after conflict resolution; no merge is authorized solely from deterministic tests.

The runtime gate after CI is credentialed demo execution producing representative M5/M15/H1/H4 XAUUSD observations. Real timing samples are required before deriving outcome lateness tolerance. Secrets must remain outside repository content.

## Safety boundary

Agent 05 remains the final deterministic permission authority and fails closed on invalid, stale or unsafe Agent 04 state. Agent 06 remains read-only and explicitly exposes `execution_enabled: false`. Historical, replay and market-data work is evidence-only and does not create trading authority.

Historical/analytics failures must never increase trading authority.

## Active Phase 2 loop

1. cTrader provider migration approved by product owner.
2. Correct symbol-specific price scaling and deterministic tests.
3. Resolve PR #27 workflow conflict without dropping either dependency installation, timing capture, or 15-minute cadence.
4. Obtain fresh exact-head CI.
5. Run credentialed demo Agent 02 and verify M5/M15/H1/H4 artifacts.
6. Collect representative 15-minute timing samples.
7. Derive and enforce outcome lateness tolerance from measured evidence.
8. Extend directional/performance analytics only after the observation-time reference-price contract is exercised against representative evidence; analytics failures must never increase authority.
9. Harden historical indexing only when evidence volume justifies it.
