# RAHUL AI TEAM — READ-ONLY HISTORICAL EVIDENCE ANALYTICS

from history.observations import (
    HORIZONS,
    _parse_timestamp,
    _read_jsonl,
    _validate_existing_outcome,
    _validate_trader_view,
)


def _validate_observation(record):
    """Validate persisted prediction evidence before analytics can count it."""
    if not isinstance(record, dict):
        raise ValueError("invalid observation record")
    observation_id = record.get("observation_id")
    if not isinstance(observation_id, str) or not observation_id.strip():
        raise ValueError("observation_id is required")
    if record.get("schema_version") != 1:
        raise ValueError("unsupported observation schema_version")
    _parse_timestamp(record.get("observed_at"), "observed_at")
    prediction = record.get("prediction")
    _validate_trader_view(prediction)
    if prediction.get("source") != "TraderView" or prediction.get("mode") != "READ_ONLY":
        raise ValueError("observation prediction must originate from read-only TraderView")
    if prediction.get("execution_enabled") is not False:
        raise ValueError("observation prediction must not enable execution")
    return observation_id


def _coverage_status(count, total):
    if total == 0 or count == 0:
        return "EMPTY"
    if count == total:
        return "COMPLETE"
    return "PARTIAL"


def _empty_report(health):
    return {
        "health": health,
        "mode": "READ_ONLY",
        "execution_enabled": False,
        "observations": 0,
        "outcomes": 0,
        "coverage_by_horizon": {horizon: 0 for horizon in HORIZONS},
        "missing_by_horizon": {horizon: 0 for horizon in HORIZONS},
        "coverage_status_by_horizon": {horizon: "EMPTY" for horizon in HORIZONS},
        "complete_observations": 0,
        "incomplete_observations": 0,
    }


def build_evidence_coverage(observation_path, outcome_path):
    """Return read-only coverage intelligence, failing closed to zero authority on corrupt evidence."""
    try:
        observations = _read_jsonl(observation_path)
        observation_ids = []
        seen_ids = set()
        for record in observations:
            observation_id = _validate_observation(record)
            if observation_id in seen_ids:
                raise ValueError("duplicate observation_id in history")
            seen_ids.add(observation_id)
            observation_ids.append(observation_id)

        coverage = {horizon: 0 for horizon in HORIZONS}
        outcome_keys = set()
        for record in _read_jsonl(outcome_path):
            validated = _validate_existing_outcome(record, observation_path)
            key = (validated["observation_id"], validated["horizon"])
            if key in outcome_keys:
                raise ValueError("duplicate outcome key in history")
            outcome_keys.add(key)
            coverage[validated["horizon"]] += 1

        complete = sum(
            1
            for observation_id in observation_ids
            if all((observation_id, horizon) in outcome_keys for horizon in HORIZONS)
        )
        total = len(observation_ids)
        missing = {horizon: total - coverage[horizon] for horizon in HORIZONS}
        statuses = {
            horizon: _coverage_status(coverage[horizon], total)
            for horizon in HORIZONS
        }
        return {
            "health": "SUCCESS",
            "mode": "READ_ONLY",
            "execution_enabled": False,
            "observations": total,
            "outcomes": len(outcome_keys),
            "coverage_by_horizon": coverage,
            "missing_by_horizon": missing,
            "coverage_status_by_horizon": statuses,
            "complete_observations": complete,
            "incomplete_observations": total - complete,
        }
    except (OSError, ValueError, TypeError):
        return _empty_report("FAILED")
