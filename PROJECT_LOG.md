# Rahul AI Team — Project Log

Last audited: 2026-07-30
Current branch: `phase2/orchestration-history`
Deterministic V1 merge: `da8fe5d3547bdc0605897cda49377e8f6f9cdfe5` via PR #5

This file is the persistent source of truth for architecture, recovery evidence, current health, contracts, safety policy and next work.

## Loop Engineering protocol

**Inspect → Plan → Build → Test → Observe → Critique → Fix → Retest → Integrate → Monitor → Repeat**.

Rules:
- Repository evidence beats assumptions.
- Deterministic safety gates beat model opinions.
- Generated state uses the normalized atomic `utils/json_writer.py` envelope.
- Missing, malformed, failed, stale, future-dated or degraded upstream state reduces authority, never increases it.
- No autonomous broker execution in the current architecture.
- Agent 05 is the deterministic permission boundary; Agent 06 is read-only and always exposes `execution_enabled: false`.
- Historical collection must record decisions/outcomes without retroactively mutating the original prediction.

## V1 baseline — MERGED

Architecture:
`Agent 02 Technical` + `Agent 03 Macro/News` → **Agent 04 Decision** → **Agent 05 Permission** → **Agent 06 Alert Gateway (read-only)**.

Agent 01 remains isolated. Keltner Bot 2.0 remains a separate project.

PR #5 was merged after latest effective V1 HEAD `8501a1d0` passed GitHub Actions Tests #75 including the unit-test step. The merged V1 includes multi-timeframe fusion, explicit Agent 03 observed-headline risk, freshness validation, fail-closed permission logic, Agent 06 read-only alerts, synthetic contract tests and updated README.

## Stable V1 contracts

- Agent 02 max age at Agent 04: 20 minutes.
- Agent 03 max age at Agent 04: 6 hours.
- Agent 04 max age at Agent 05: 15 minutes.
- Agent 05 max age at Agent 06: 15 minutes.
- Agent 03 RSS risk is LOW/MEDIUM/HIGH only; EXTREME requires a future validated scheduled-event source.
- Degraded state cannot become autonomous authority.
- Agent 06 has no execution path.

## Phase 2 objective — ACTIVE

Build safe automation/orchestration and immutable historical state/outcome collection so Rahul AI Team can measure what it believed, what permission it issued, and what XAUUSD subsequently did.

Phase 2 is observational infrastructure, not autonomous trading.

### Planned Phase 2 data flow

`V1 pipeline run` → `snapshot recorder` → `append-only observation record` → later `outcome evaluator` → performance analytics.

The recorder should preserve:
- observation/run ID;
- observation timestamp;
- Agent 02/03/04/05/06 generated timestamps and health;
- fused technical context and macro context needed for analysis;
- Agent 04 decision/confidence/risk/reasons;
- Agent 05 permission/reason;
- Agent 06 alert/read-only status;
- XAUUSD reference price at observation time when available;
- outcome fields initially null/unresolved, populated later by a separate evaluator;
- schema version.

### Safety/data integrity requirements

1. Never overwrite the original prediction fields when outcomes become known.
2. Outcome evaluation must be a separate step with explicit horizons (for example +15m/+1h/+4h) rather than vague win/loss labels.
3. Missing source state must be recorded honestly; never fabricate market context.
4. Historical collection failure must not weaken Agent 05/06 safety behavior.
5. No secrets/API keys in history records.
6. No broker/order methods in Phase 2 orchestration.
7. Tests must prove append-only/idempotent behavior before automation is enabled.

## Active engineering loop

1. Audit existing workflows and state I/O against the merged V1 baseline.
2. Design versioned observation schema and deterministic snapshot recorder.
3. Add unit tests for complete, degraded, missing and duplicate snapshot cases.
4. Add an orchestration runner that executes/consumes the V1 stages without introducing broker execution.
5. Add workflow automation only after recorder/orchestrator tests are green.
6. Design outcome evaluator and historical performance metrics after reliable snapshots exist.
7. Update README and this log after every meaningful milestone.
8. Open a Phase 2 PR only after the first coherent, tested slice is ready.

## Post-Phase 2 roadmap

Historical outcome collection → performance analytics/calibration → architecture hardening → validated integrations → ML-assisted intelligence/feedback → V2.

ML initially augments deterministic intelligence and calibration; it does not replace fail-closed safety gates.
