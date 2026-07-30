# RAHUL AI TEAM — APPEND-ONLY HISTORICAL OBSERVATIONS

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


HORIZONS = ("15m", "1h", "4h")


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _timestamp(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include timezone information")
    return value


def _read_jsonl(path):
    target = Path(path)
    if not target.exists():
        return []
    records = []
    with target.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"corrupt JSONL at line {line_number}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"invalid JSONL record at line {line_number}")
            records.append(record)
    return records


def build_observation(trader_view, observed_at=None):
    """Create an immutable prediction snapshot with separately appendable outcomes."""
    if not isinstance(trader_view, dict):
        raise ValueError("trader_view must be a dictionary")
    observed_at = _timestamp(observed_at or datetime.now(timezone.utc).isoformat(), "observed_at")
    prediction = {
        "symbol": trader_view.get("symbol", "XAUUSD"),
        "decision": trader_view.get("decision", "NO_TRADE"),
        "permission": trader_view.get("permission", "BLOCK_TRADING"),
        "confidence": trader_view.get("confidence", 0),
        "risk": trader_view.get("risk", "EXTREME"),
        "macro_bias": trader_view.get("macro_bias", "NEUTRAL"),
        "news_risk": trader_view.get("news_risk", "HIGH"),
        "timeframe_conflict": trader_view.get("timeframe_conflict", "HIGH"),
        "trend_votes": trader_view.get("trend_votes", {}),
        "fresh": bool(trader_view.get("fresh", False)),
        "execution_enabled": False,
    }
    fingerprint = hashlib.sha256(_canonical({"observed_at": observed_at, "prediction": prediction}).encode()).hexdigest()[:20]
    return {
        "observation_id": fingerprint,
        "observed_at": observed_at,
        "prediction": prediction,
        "outcomes": {},
        "schema_version": 1,
    }


def append_observation(path, observation):
    """Append once by observation_id. Existing or corrupt history is never rewritten."""
    if not isinstance(observation, dict) or not observation.get("observation_id"):
        raise ValueError("observation_id is required")
    _timestamp(observation.get("observed_at"), "observed_at")
    if observation.get("schema_version") != 1:
        raise ValueError("unsupported observation schema_version")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    existing_ids = {record.get("observation_id") for record in _read_jsonl(target)}
    if observation["observation_id"] in existing_ids:
        return False
    with target.open("a", encoding="utf-8") as handle:
        handle.write(_canonical(observation) + "\n")
    return True


def build_outcome(observation_id, horizon, reference_price, measured_at=None):
    """Build a separate outcome event; never mutate the original prediction record."""
    if not isinstance(observation_id, str) or not observation_id.strip():
        raise ValueError("observation_id is required")
    if horizon not in HORIZONS:
        raise ValueError("unsupported horizon")
    if isinstance(reference_price, bool) or not isinstance(reference_price, (int, float)) or not math.isfinite(reference_price) or reference_price <= 0:
        raise ValueError("reference_price must be a finite positive number")
    measured_at = _timestamp(measured_at or datetime.now(timezone.utc).isoformat(), "measured_at")
    return {
        "observation_id": observation_id,
        "horizon": horizon,
        "reference_price": float(reference_price),
        "measured_at": measured_at,
        "schema_version": 1,
    }


def append_outcome(path, outcome, observation_path=None):
    """Append one outcome per observation/horizon; fail closed on corrupt or orphaned evidence."""
    if not isinstance(outcome, dict):
        raise ValueError("outcome must be a dictionary")
    observation_id = outcome.get("observation_id")
    horizon = outcome.get("horizon")
    validated = build_outcome(observation_id, horizon, outcome.get("reference_price"), outcome.get("measured_at"))
    if outcome.get("schema_version") != 1:
        raise ValueError("unsupported outcome schema_version")
    if observation_path is not None:
        observation_ids = {record.get("observation_id") for record in _read_jsonl(observation_path)}
        if observation_id not in observation_ids:
            raise ValueError("outcome references unknown observation_id")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    keys = set()
    for record in _read_jsonl(target):
        key = (record.get("observation_id"), record.get("horizon"))
        if None in key:
            raise ValueError("invalid existing outcome record")
        keys.add(key)
    key = (observation_id, horizon)
    if key in keys:
        return False
    with target.open("a", encoding="utf-8") as handle:
        handle.write(_canonical(validated) + "\n")
    return True
