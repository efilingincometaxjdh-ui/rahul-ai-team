# RAHUL AI TEAM — AGENT 05: PERMISSION ENGINE

from permissions.engine import PermissionEngine
from utils.json_reader import read_state
from utils.json_writer import write_state


def build_permission(decision_state):
    errors = []
    if not decision_state:
        errors.append("Agent04 decision state missing")
    elif decision_state.get("status") == "FAILED":
        errors.append("Agent04 decision state failed")

    if errors:
        result = {"permission": "BLOCK_TRADING", "reason": "; ".join(errors)}
        return result, "FAILED", errors

    decision = decision_state.get("data", {})
    result = PermissionEngine().evaluate(decision)

    if result["permission"] == "BLOCK_TRADING":
        status = "DEGRADED" if decision_state.get("status") != "FAILED" else "FAILED"
    elif decision_state.get("status") == "DEGRADED":
        # Degraded upstream intelligence cannot silently become full authority.
        result = {
            "permission": "CAUTION",
            "reason": "Agent04 is degraded; human review required.",
        }
        status = "DEGRADED"
    else:
        status = "SUCCESS"

    return result, status, errors


def main():
    decision_state = read_state("decision.json")
    data, status, errors = build_permission(decision_state)
    write_state(
        agent="Agent05",
        version="0.1",
        filename="permission.json",
        data=data,
        status=status,
        errors=errors,
        metadata={"input": "decision.json", "policy": "fail-closed"},
    )
    print(f"Agent05 health: {status} | Permission: {data['permission']}")
    if status == "FAILED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
