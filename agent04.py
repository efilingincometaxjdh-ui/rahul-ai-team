# RAHUL AI TEAM — AGENT 04: DECISION ENGINE

from decision.engine import DecisionEngine
from utils.json_reader import read_state
from utils.json_writer import write_state

TIMEFRAME_WEIGHTS = {"H4": 4, "H1": 3, "M15": 2, "M5": 1}
REQUIRED_TECHNICAL_FIELDS = ("ema20", "ema50", "rsi", "adx", "trend")


def _valid_technical(technical):
    return isinstance(technical, dict) and all(
        technical.get(field) is not None for field in REQUIRED_TECHNICAL_FIELDS
    )


def fuse_technical_state(agent02_state):
    """Fuse every usable Agent 02 timeframe, weighted toward higher timeframes."""
    data = agent02_state.get("data", {}) if isinstance(agent02_state, dict) else {}
    usable = {
        timeframe: data[timeframe]
        for timeframe in TIMEFRAME_WEIGHTS
        if _valid_technical(data.get(timeframe))
    }
    if not usable:
        return None, {"usable_timeframes": [], "trend_votes": {}}

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
    }
    return technical, metadata


def normalize_macro(agent03_state):
    data = agent03_state.get("data", {}) if isinstance(agent03_state, dict) else {}
    return {
        "gold_bias": data.get("gold_bias", "NEUTRAL"),
        # Agent 03 v0.1 exposes impact counts rather than an explicit risk enum.
        # HIGH is conservative without inventing EXTREME event semantics.
        "news_risk": "HIGH" if data.get("high_impact_count", 0) else "LOW",
    }


def build_decision(agent02_state, agent03_state):
    errors = []
    if not isinstance(agent02_state, dict) or agent02_state.get("status") not in {"SUCCESS", "DEGRADED"}:
        errors.append("Agent02 state unavailable, malformed, or failed")
    if not isinstance(agent03_state, dict) or agent03_state.get("status") not in {"SUCCESS", "DEGRADED"}:
        errors.append("Agent03 state unavailable, malformed, or failed")

    technical, fusion_metadata = fuse_technical_state(agent02_state or {})
    if technical is None:
        errors.append("No complete technical timeframe available")

    if errors:
        return {
            "decision": "NO_TRADE",
            "confidence": 0,
            "risk": "EXTREME",
            "reasons": errors,
        }, "FAILED", errors, {"technical_fusion": fusion_metadata}

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
        "inputs": ["agent02.json", "agent03.json"],
    }
    return result, status, errors, metadata


def main():
    agent02_state = read_state("agent02.json")
    agent03_state = read_state("agent03.json")
    data, status, errors, metadata = build_decision(agent02_state, agent03_state)
    write_state(
        agent="Agent04",
        version="0.2",
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
