# Rahul AI Team — Project Log

Last audited: 2026-07-31
Branch: `main` + draft PR #14
Phase: **Phase 2 — evidence infrastructure**

This file is the persistent source of truth. Loop Engineering: **Inspect → Plan → Build → Test → Observe → Critique → Fix → Retest → Integrate → Monitor → Repeat**.

## Non-negotiable architecture and safety

`Agent 02 Technical` + `Agent 03 Macro/News` → **Agent 04 Decision** → **Agent 05 Permission** → **Agent 06 Alert Gateway (read-only)** → **Trader View / historical evidence**.

- Repository evidence beats assumptions; deterministic safety gates beat model opinions.
- Agent 05 fails closed on NO_TRADE, invalid/stale/unknown inputs, invalid confidence, EXTREME risk and unsafe state.
- Agent 06 is read-only and always exposes `execution_enabled: false`.
- Historical/analytics infrastructure is evidence-only and can never increase trading authority.
- Agent 01 remains isolated because it overlaps Agent 03 and contains a legacy bot-action path. Do not integrate without deliberate overlap resolution.
- No autonomous execution, broker integration, paid services or committed credentials.
- Keltner Bot 2.0 remains separate.

## Integrated deterministic V1

PR #5 integrated deterministic V1 after Tests #75. Agent 02 produces M5/M15/H1/H4 technical state. Agent 03 v0.2 produces deterministic macro/news intelligence and cannot infer EXTREME from RSS. Agent 04 v0.4 uses H4=4, H1=3, M15=2, M5=1 weighted fusion and exposes ALIGNED/CONFLICT/NEUTRAL metadata without changing decision authority. Agent 05 v0.2 is the final fail-closed permission gate. Agent 06 v0.1 is read-only. Trader View v0.2 exposes permission plus explicit MTF intelligence while execution remains disabled.

Freshness contracts: Agent02→04 ≤20m; Agent03→04 ≤6h; Agent04→05 ≤15m; Agent05→06 ≤15m. Missing, malformed, failed, stale, future-dated or degraded state reduces authority and never increases it.

## CI / integration evidence

- `.github/workflows/tests.yml`: `python -m unittest discover -s tests -v`, Python 3.11, push + pull request.
- Recovery `bdb0e7e`: Tests #43 SUCCESS.
- MTF/fail-closed `1f988e98`: Tests #53 SUCCESS.
- Freshness/end-to-end `06d79b5d`: Tests #67 SUCCESS.
- Deterministic V1 `8501a1d0`: Tests #75 SUCCESS; PR #5 merged.
- Historical observations `27f54dca`: Tests #86 SUCCESS; PR #6 merged.
- Outcome integrity `7289267b`: Tests #93 SUCCESS; PR #7 merged.
- Trader View boundary `893fd357`: Tests #100 SUCCESS; PR #8 merged.
- Outcome timing `726dcdbc`: Tests #107 SUCCESS; PR #9 merged.
- Agent04 MTF `78ade145`: Tests #112 SUCCESS; PR #10 merged.
- Trader View MTF `7e242bbd`: Tests #119 SUCCESS; PR #11 merged.
- Historical MTF `7720bc5b`: Tests #127 SUCCESS; PR #12 merged.
- Observation orchestration `ab1d70d9`: Tests #134 SUCCESS; PR #13 merged.
- Draft PR #14 `phase2/reference-price-contract`: reference-price contract + deterministic tests committed; exact-HEAD CI pending. Do not integrate before clean evidence.

## Phase 2 evidence contract

PR #6 introduced immutable prediction snapshots, deterministic IDs, append-only JSONL and separate 15m/1h/4h outcomes. PR #7 added one-outcome-per-observation/horizon integrity, orphan rejection, timestamp/schema validation, finite positive-price validation and corrupt-history fail-closed behavior. PR #8 requires valid read-only XAUUSD Trader View input. PR #9 enforces `measured_at >= observed_at + horizon` against exactly one source observation. PR #10–12 carry explicit Agent04 MTF alignment/conflict intelligence through Trader View into immutable evidence. PR #13 adds an evidence-only Trader View observation collector; it does not schedule itself, fetch prices, write current permission state or execute trades.

Draft PR #14 adds a provider-neutral reference-price admission contract before any live outcome collector is allowed. A reference quote must explicitly be `XAUUSD`, `SPOT`, quoted in `USD`, have a named provider, finite positive price, timezone-aware observation timestamp, and `requires_credentials: false`. Futures, ETFs, proxy instruments, credential-requiring sources and malformed quotes fail closed. This contract validates evidence only and is not wired to Agent05/06 authority.

Provider research on 2026-07-31 found Yahoo Finance's `GC=F` is COMEX gold futures and its page identifies the quote as delayed. It is therefore **rejected as an XAUUSD spot outcome source**, not silently substituted. No live reference-price provider has yet been accepted.

## Remaining risks / technical debt

1. No zero-cost, credential-free live **spot XAUUSD** reference source has yet passed the new contract.
2. Outcome timing has a minimum horizon but no maximum lateness tolerance; choose only after collection-cadence evidence exists.
3. Observation cadence is intentionally unscheduled until source/cadence evidence is adequate.
4. Historical duplicate checks scan JSONL; harden indexing only when volume justifies it.
5. Agent 03 still lacks a validated scheduled-event calendar, so EXTREME event windows remain intentionally unavailable.
6. Freshness thresholds need later empirical validation.

## Active Phase 2 loop

1. Obtain exact-HEAD CI for PR #14; diagnose/fix failures and integrate only if clean, mergeable and routine.
2. Continue validating a zero-cost, credential-free **spot XAUUSD** source; reject futures/proxies rather than corrupt outcome evidence.
3. Only after a source is validated, build an evidence-only outcome collector for +15m/+1h/+4h.
4. Define lateness tolerance from real collection cadence.
5. Build analytics only after enough trustworthy observations/outcomes exist; analytics failures must never increase authority.
