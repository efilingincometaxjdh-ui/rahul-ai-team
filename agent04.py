# RAHUL AI TEAM — AGENT 04: XAUUSD INTELLIGENCE FUSION

from decision.engine import build_decision
from utils.json_reader import read_state
from utils.json_writer import write_state


def main():
    print("AGENT 04 — XAUUSD INTELLIGENCE FUSION")
    agent02 = read_state("agent02.json", required=True)
    agent03 = read_state("agent03.json", required=True)
    decision = build_decision(agent02, agent03)
    source_health = decision["source_health"]
    status = "SUCCESS" if all(v == "SUCCESS" for v in source_health.values()) else "DEGRADED"
    write_state(
        agent="Agent04", version="0.1", filename="agent04.json", data=decision,
        status=status, metadata={"inputs": ["agent02.json", "agent03.json"]},
    )
    print(f"Agent04: {decision['bias']} | confidence {decision['confidence']}% | {decision['setup_quality']}")


if __name__ == "__main__":
    main()
