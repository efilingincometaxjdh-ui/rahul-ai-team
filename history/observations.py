# RAHUL AI TEAM — APPEND-ONLY HISTORICAL OBSERVATIONS

import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

HORIZONS = ("15m", "1h", "4h")
HORIZON_DELTAS = {"15m": timedelta(minutes=15), "1h": timedelta(hours=1), "4h": timedelta(hours=4)}
KNOWN_DECISIONS = {"BUY", "SELL", "NO_TRADE"}
KNOWN_PERMISSIONS = {"ALLOW_BUYS", "ALLOW_SELLS", "ALLOW_BOTH", "CAUTION", "BLOCK_TRADING"}
KNOWN_RISKS = {"LOW", "MEDIUM", "HIGH", "EXTREME"}
KNOWN_CONFLICTS = {"LOW", "MEDIUM", "HIGH"}
KNOWN_ALIGNMENTS = {"ALIGNED", "CONFLICT", "NEUTRAL"}
KNOWN_TRENDS = {"BULLISH", "BEARISH", "NEUTRAL"}
KNOWN_TIMEFRAMES = {"H4", "H1", "M15", "M5"}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _parse_timestamp(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include timezone information")
    return parsed


def _timestamp(value, field):
    _parse_timestamp(value, field)
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


def _validate_alignment_intelligence(trader_view):
    alignment = str(trader_view.get("timeframe_alignment", "NEUTRAL")).upper()
    if alignment not in KNOWN_ALIGNMENTS:
        raise ValueError("unknown trader_view timeframe_alignment")
    trends = trader_view.get("timeframe_trends", {})
    if not isinstance(trends, dict):
        raise ValueError("trader_view timeframe_trends must be a dictionary")
    normalized_trends = {}
    for timeframe, trend in trends.items():
        if timeframe not in KNOWN_TIMEFRAMES:
            raise ValueError("unknown trader_view timeframe_trends timeframe")
        normalized = str(trend).upper()
        if normalized not in KNOWN_TRENDS:
            raise ValueError("unknown trader_view timeframe trend")
        normalized_trends[timeframe] = normalized
    conflicts = {}
    for field in ("higher_timeframe_conflict", "lower_timeframe_conflict", "cross_group_conflict"):
        value = trader_view.get(field, False)
        if not isinstance(value, bool):
            raise ValueError(f"trader_view {field} must be boolean")
        conflicts[field] = value
    return alignment, normalized_trends, conflicts


def _validate_trader_view(trader_view):
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
    return _validate_alignment_intelligence(trader_view)


def build_observation(trader_view, observed_at=None):
    alignment, timeframe_trends, conflicts = _validate_trader_view(trader_view)
    observed_at = _timestamp(observed_at or datetime.now(timezone.utc).isoformat(), "observed_at")
    prediction = {
        "symbol": trader_view["symbol"], "decision": trader_view["decision"],
        "permission": trader_view["permission"], "confidence": trader_view["confidence"],
        "risk": trader_view["risk"], "macro_bias": trader_view.get("macro_bias", "NEUTRAL"),
        "news_risk": trader_view.get("news_risk", "HIGH"), "timeframe_conflict": trader_view["timeframe_conflict"],
        "timeframe_alignment": alignment, "timeframe_trends": timeframe_trends,
        "higher_timeframe_conflict": conflicts["higher_timeframe_conflict"],
        "lower_timeframe_conflict": conflicts["lower_timeframe_conflict"],
        "cross_group_conflict": conflicts["cross_group_conflict"],
        "trend_votes": trader_view.get("trend_votes", {}), "fresh": trader_view["fresh"],
        "execution_enabled": False, "source": "TraderView", "mode": "READ_ONLY",
    }
    fingerprint = hashlib.sha256(_canonical({"observed_at": observed_at, "prediction": prediction}).encode()).hexdigest()[:20]
    return {"observation_id": fingerprint, "observed_at": observed_at, "prediction": prediction, "outcomes": {}, "schema_version": 1}


def append_observation(path, observation):
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
    if not isinstance(observation_id, str) or not observation_id.strip():
        raise ValueError("observation_id is required")
    if horizon not in HORIZONS:
        raise ValueError("unsupported horizon")
    if isinstance(reference_price, bool) or not isinstance(reference_price, (int, float)) or not math.isfinite(reference_price) or reference_price <= 0:
        raise ValueError("reference_price must be a finite positive number")
    measured_at = _timestamp(measured_at or datetime.now(timezone.utc).isoformat(), "measured_at")
    return {"observation_id": observation_id, "horizon": horizon, "reference_price": float(reference_price), "measured_at": measured_at, "schema_version": 1}


def _source_observation(observation_path, observation_id):
    if observation_path is None:
        raise ValueError("observation_path is required for outcome integrity")
    matches = [record for record in _read_jsonl(observation_path) if record.get("observation_id") == observation_id]
    if not matches:
        raise ValueError("outcome references unknown observation_id")
    if len(matches) != 1:
        raise ValueError("duplicate source observation_id in history")
    observation = matches[0]
    if observation.get("schema_version") != 1:
        raise ValueError("unsupported source observation schema_version")
    _parse_timestamp(observation.get("observed_at"), "observed_at")
    return observation


def _validate_existing_outcome(record, observation_path):
    """Semantically validate persisted outcome evidence before it can occupy an idempotency key."""
    if not isinstance(record, dict):
        raise ValueError("invalid existing outcome record")
    if record.get("schema_version") != 1:
        raise ValueError("unsupported existing outcome schema_version")
    validated = build_outcome(
        record.get("observation_id"), record.get("horizon"),
        record.get("reference_price"), record.get("measured_at"),
    )
    observation = _source_observation(observation_path, validated["observation_id"])
    observed_at = _parse_timestamp(observation["observed_at"], "observed_at")
    measured_at = _parse_timestamp(validated["measured_at"], "measured_at")
    if measured_at < observed_at + HORIZON_DELTAS[validated["horizon"]]:
        raise ValueError(f"existing outcome measured_at is earlier than the {validated['horizon']} horizon")
    return validated


def append_outcome(path, outcome, observation_path=None):
    """Append one correctly timed outcome per observation/horizon; fail closed on bad evidence."""
    if not isinstance(outcome, dict):
        raise ValueError("outcome must be a dictionary")
    observation_id = outcome.get("observation_id")
    horizon = outcome.get("horizon")
    validated = build_outcome(observation_id, horizon, outcome.get("reference_price"), outcome.get("measured_at"))
    if outcome.get("schema_version") != 1:
        raise ValueError("unsupported outcome schema_version")
    observation = _source_observation(observation_path, observation_id)
    observed_at = _parse_timestamp(observation["observed_at"], "observed_at")
    measured_at = _parse_timestamp(validated["measured_at"], "measured_at")
    if measured_at < observed_at + HORIZON_DELTAS[horizon]:
        raise ValueError(f"measured_at is earlier than the {horizon} horizon")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    keys = set()
    for record in _read_jsonl(target):
        existing = _validate_existing_outcome(record, observation_path)
        key = (existing["observation_id"], existing["horizon"])
        if key in keys:
            raise ValueError("duplicate outcome key in existing history")
        keys.add(key)
    key = (observation_id, horizon)
    if key in keys:
        return False
    with target.open("a", encoding="utf-8") as handle:
        handle.write(_canonical(validated) + "\n")
    return True
