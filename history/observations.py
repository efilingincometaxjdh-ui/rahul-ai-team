# RAHUL AI TEAM — APPEND-ONLY HISTORICAL OBSERVATIONS

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


HORIZONS = ("15m", "1h", "4h")
KNOWN_DECISIONS = {"BUY", "SELL", "NO_TRADE"}
KNOWN_PERMISSIONS = {"ALLOW_BUYS", "ALLOW_SELLS", "ALLOW_BOTH", "CAUTION", "BLOCK_TRADING"}
KNOWN_RISKS = {"LOW", "MEDIUM", "HIGH", "EXTREME"}
KNOWN_CONFLICTS = {"LOW", "MEDIUM", "HIGH"}


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


def _validate_trader_view(trader_view):
    """Require a safe, read-only Trader View before it can become historical evidence."""
    if not isinstance(trader_view, dict):
        raise ValueError("trader_view must be a dictionary")
    if trader_view.get("symbol") != "XAUUSD":
        raise ValueError("trader_view symbol must be XAUUSD")
    if trader_view.get("mode") != "READ_ONLY":
        raise ValueError("trader_view mode must be READ_ONLY")
    if trader_view.get("execution_enabled") is not False:
        raise ValueError("trader_view must not enable execution")
    if trader_view.get("decision") not in KNOWN_DECISIONS:
        raise ValueError("unknown trader_view decision")
    if trader_view.get("permission") not in KNOWN_PERMISSIONS:
        raise ValueError("unknown trader_view permission")
    if trader_view.get("risk") not in KNOWN_RISKS:
        raise ValueError("unknown trader_view risk")
    if trader_view.get("timeframe_conflict") not in KNOWN_CONFLICTS:
        raise ValueError("unknown trader_view timeframe_conflict")
    confidence = trader_view.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 100:
        raise ValueError("trader_view confidence must be between 0 and 100")
    fresh = trader_view.get("fresh")
    if not isinstance(fresh, bool):
        raise ValueError("trader_view fresh must be boolean")

    permission = trader_view["permission"]
    decision = trader_view["decision"]
    if decision == "NO_TRADE" and permission.startswith("ALLOW_"):
        raise ValueError("NO_TRADE cannot carry ALLOW permission")
    if permission == "ALLOW_BUYS" and decision != "BUY":
        raise ValueError("ALLOW_BUYS requires BUY decision")
    if permission == "ALLOW_SELLS" and decision != "SELL":
        raise ValueError("ALLOW_SELLS requires SELL decision")
    if not fresh and permission.startswith("ALLOW_"):
        raise ValueError("stale Trader View cannot carry ALLOW permission")


def build_observation(trader_view, observed_at=None):
    """Create an immutable prediction snapshot from the read-only Trader View only."""
    _validate_trader_view(trader_view)
    observed_at = _timestamp(observed_at or datetime.now(timezone.utc).isoformat(), "observed_at")
    prediction = {
        "symbol": trader_view["symbol"],
        "decision": trader_view["decision"],
        "permission": trader_view["permission"],
        "confidence": trader_view["confidence"],
        "risk": trader_view["risk"],
        "macro_bias": trader_view.get("macro_bias", "NEUTRAL"),
        "news_risk": trader_view.get("news_risk", "HIGH"),
        "timeframe_conflict": trader_view["timeframe_conflict"],
        "trend_votes": trader_view.get("trend_votes", {}),
        "fresh": trader_view["fresh"],
        "execution_enabled": False,
        "source": "TraderView",
        "mode": "READ_ONLY",
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
