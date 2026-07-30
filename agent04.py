# RAHUL AI TEAM — AGENT 04: DECISION ENGINE

from decision.engine import DecisionEngine
from utils.json_reader import read_state
from utils.json_writer import write_state
from utils.state_validation import validate_state_freshness

TIMEFRAME_WEIGHTS = {"H4": 4, "H1": 3, "M15": 2, "M5": 1}
REQUIRED_TECHNICAL_FIELDS = ("ema20", "ema50", "rsi", "adx", "trend")
AGENT02_MAX_AGE_SECONDS = 20 * 60
AGENT03_MAX_AGE_SECONDS = 6 * 60 * 60


def _valid_technical(technical):
    return isinstance(technical, dict) and all(
        technical.get(field) is not None for field in REQUIRED_TECHNICAL_FIELDS
    )


def _alignment_metadata(usable):
    """Describe MTF agreement without changing deterministic decision authority."""
    trends = {tf: str(value["trend"]).lower() for tf, value in usable.items()}
    directional = {tf: trend for tf, trend in trends.items() if trend in {"bullish", "bearish"}}
    unique = set(directional.values())

    if not directional:
        state = "NEUTRAL"
    elif len(unique) == 1:
        state = "ALIGNED"
    else:
        state = "CONFLICT"

    higher = {tf: directional[tf] for tf in ("H4", "H1") if tf in directional}
    lower = {tf: directional[tf] for tf in ("M15", "M5") if tf in directional}
    higher_conflict = len(set(higher.values())) > 1
    lower_conflict = len(set(lower.values())) > 1
    cross_group_conflict = bool(higher and lower and set(higher.values()) != set(lower.values()))

    return {
        "state": state,
        "timeframe_trends": trends,
        "higher_timeframes": higher,
        "lower_timeframes": lower,
        "higher_timeframe_conflict": higher_conflict,
        "lower_timeframe_conflict": lower_conflict,
        "cross_group_conflict": cross_group_conflict,
    }


def fuse_technical_state(agent02_state):
    """Fuse every usable Agent 02 timeframe, weighted toward higher timeframes."""
    data = agent02_state.get("data", {}) if isinstance(agent02_state, dict) else {}
    usable = {
        timeframe: data[timeframe]
        for timeframe in TIMEFRAME_WEIGHTS
        if _valid_technical(data.get(timeframe))
    }
    if not usable:
        return None, {"usable_timeframes": [], "trend_votes": {}, "alignment": _alignment_metadata({})}

    total_weight = sum(TIMEFRAME_WEIGHTS[timeframe] for timeframe in usable)
    bullish_weight = sum(
        TIMEFRAME_WEIGHTS[timeframe]
        for timeframe, technical in usable.items()
        if str(technical["trend"]).lower() == "bullish"
    )
    bearish_weight = sum(
        TIMEFRAME_WEIGHTS[timeframe]
        for timeframe, technical in usable.items()
        if str(technical["trend"]).lower() == "bearish"
    )

    if bullish_weight > bearish_weight:
        trend = "Bullish"
    elif bearish_weight > bullish_weight:
        trend = "Bearish"
    else:
        trend = "Neutral"

    def weighted_average(field):
        return sum(
            float(technical[field]) * TIMEFRAME_WEIGHTS[timeframe]
            for timeframe, technical in usable.items()
        ) / total_weight

    technical = {
        "ema20": weighted_average("ema20"),
        "ema50": weighted_average("ema50"),
        "rsi": weighted_average("rsi"),
        "adx": weighted_average("adx"),
        "trend": trend,
    }
    metadata = {
        "usable_timeframes": list(usable.keys()),
        "timeframe_weights": {tf: TIMEFRAME_WEIGHTS[tf] for tf in usable},
        "trend_votes": {"bullish": bullish_weight, "bearish": bearish_weight},
        "alignment": _alignment_metadata(usable),
    }
    return technical, metadata


def normalize_macro(agent03_state):
    data = agent03_state.get("data", {}) if isinstance(agent03_state, dict) else {}
    return {
        "gold_bias": data.get("gold_bias", "NEUTRAL"),
        "news_risk": data.get("news_risk", "HIGH"),
    }


def build_decision(agent02_state, agent03_state, now=None):
    errors = []
    freshness = {}
    inputs = (
        ("Agent02", agent02_state, AGENT02_MAX_AGE_SECONDS),
        ("Agent03", agent03_state, AGENT03_MAX_AGE_SECONDS),
    )
    for name, state, max_age in inputs:
        if not isinstance(state, dict) or state.get("status") not in {"SUCCESS", "DEGRADED"}:
            errors.append(f"{name} state unavailable, malformed, or failed")
            freshness[name] = {"fresh": False, "reason": "invalid health envelope"}
            continue
        fresh, reason, age = validate_state_freshness(state, max_age, now=now)
        freshness[name] = {"fresh": fresh, "reason": reason, "age_seconds": age, "max_age_seconds": max_age}
        if not fresh:
            errors.append(f"{name} state rejected: {reason}")

    technical, fusion_metadata = fuse_technical_state(agent02_state or {})
    if technical is None:
        errors.append("No complete technical timeframe available")

    if errors:
        return {
            "decision": "NO_TRADE",
            "confidence": 0,
            "risk": "EXTREME",
            "reasons": errors,
        }, "FAILED", errors, {"technical_fusion": fusion_metadata, "freshness": freshness}

    macro = normalize_macro(agent03_state)
    result = DecisionEngine().evaluate(macro, technical)

    upstream_degraded = any(
        state.get("status") == "DEGRADED" for state in (agent02_state, agent03_state)
    )
    status = "DEGRADED" if upstream_degraded else "SUCCESS"
    if upstream_degraded:
        result["reasons"].append("One or more upstream agents are degraded")

    metadata = {
        "technical_fusion": fusion_metadata,
        "freshness": freshness,
        "inputs": ["agent02.json", "agent03.json"],
    }
    return result, status, errors, metadata


def main():
    agent02_state = read_state("agent02.json")
    agent03_state = read_state("agent03.json")
    data, status, errors, metadata = build_decision(agent02_state, agent03_state)
    write_state(
        agent="Agent04",
        version="0.4",
        filename="decision.json",
        data=data,
        status=status,
        errors=errors,
        metadata=metadata,
    )
    print(f"Agent04 health: {status} | Decision: {data['decision']} | Confidence: {data['confidence']}%")
    if status == "FAILED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
