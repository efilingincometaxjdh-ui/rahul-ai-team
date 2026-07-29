# RAHUL AI TEAM — AGENT 04: DECISION ENGINE

from decision.engine import DecisionEngine
from utils.json_reader import read_state
from utils.json_writer import write_state

PREFERRED_TIMEFRAMES = ("H1", "H4", "M15", "M5")


def select_technical_state(agent02_state):
    data = agent02_state.get("data", {}) if isinstance(agent02_state, dict) else {}
    for timeframe in PREFERRED_TIMEFRAMES:
        technical = data.get(timeframe)
        if isinstance(technical, dict):
            return technical, timeframe
    return None, None


def normalize_macro(agent03_state):
    data = agent03_state.get("data", {}) if isinstance(agent03_state, dict) else {}
    return {
        "gold_bias": data.get("gold_bias", "NEUTRAL"),
        # Agent 03 currently exposes impact counts rather than a risk enum.
        # Fail conservatively: high-impact headlines imply HIGH risk.
        "news_risk": "HIGH" if data.get("high_impact_count", 0) else "LOW",
    }


def build_decision(agent02_state, agent03_state):
    errors = []
    if not agent02_state or agent02_state.get("status") == "FAILED":
        errors.append("Agent02 state unavailable or failed")
    if not agent03_state or agent03_state.get("status") == "FAILED":
        errors.append("Agent03 state unavailable or failed")

    technical, timeframe = select_technical_state(agent02_state or {})
    if technical is None:
        errors.append("No usable technical timeframe")

    if errors:
        return {
            "decision": "NO_TRADE",
            "confidence": 0,
            "risk": "EXTREME",
            "reasons": errors,
        }, "FAILED", errors, {"technical_timeframe": timeframe}

    macro = normalize_macro(agent03_state)
    result = DecisionEngine().evaluate(macro, technical)

    upstream_degraded = any(
        state.get("status") == "DEGRADED" for state in (agent02_state, agent03_state)
    )
    status = "DEGRADED" if upstream_degraded else "SUCCESS"
    if upstream_degraded:
        result["reasons"].append("One or more upstream agents are degraded")

    metadata = {
        "technical_timeframe": timeframe,
        "inputs": ["agent02.json", "agent03.json"],
    }
    return result, status, errors, metadata


def main():
    agent02_state = read_state("agent02.json")
    agent03_state = read_state("agent03.json")
    data, status, errors, metadata = build_decision(agent02_state, agent03_state)
    write_state(
        agent="Agent04",
        version="0.1",
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
