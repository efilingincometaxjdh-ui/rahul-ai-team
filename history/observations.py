# RAHUL AI TEAM — APPEND-ONLY HISTORICAL OBSERVATIONS

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


HORIZONS = ("15m", "1h", "4h")


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def build_observation(trader_view, observed_at=None):
    """Create an immutable prediction snapshot with separately appendable outcomes."""
    if not isinstance(trader_view, dict):
        raise ValueError("trader_view must be a dictionary")
    observed_at = observed_at or datetime.now(timezone.utc).isoformat()
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
    """Append once by observation_id. Existing history is never rewritten."""
    if not isinstance(observation, dict) or not observation.get("observation_id"):
        raise ValueError("observation_id is required")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    existing_ids = set()
    if target.exists():
        with target.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    existing_ids.add(json.loads(line).get("observation_id"))
    if observation["observation_id"] in existing_ids:
        return False
    with target.open("a", encoding="utf-8") as handle:
        handle.write(_canonical(observation) + "\n")
    return True


def build_outcome(observation_id, horizon, reference_price, measured_at=None):
    """Build a separate outcome event; never mutate the original prediction record."""
    if horizon not in HORIZONS:
        raise ValueError("unsupported horizon")
    if not isinstance(reference_price, (int, float)) or reference_price <= 0:
        raise ValueError("reference_price must be positive")
    return {
        "observation_id": observation_id,
        "horizon": horizon,
        "reference_price": float(reference_price),
        "measured_at": measured_at or datetime.now(timezone.utc).isoformat(),
        "schema_version": 1,
    }
