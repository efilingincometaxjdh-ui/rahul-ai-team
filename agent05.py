# RAHUL AI TEAM — AGENT 05: PERMISSION ENGINE

from permissions.engine import PermissionEngine
from utils.json_reader import read_state
from utils.json_writer import write_state
from utils.state_validation import validate_state_freshness

AGENT04_MAX_AGE_SECONDS = 15 * 60


def build_permission(decision_state, now=None):
    errors = []
    freshness = {"fresh": False, "reason": "not evaluated"}
    if not isinstance(decision_state, dict):
        errors.append("Agent04 decision state missing or malformed")
    elif decision_state.get("status") not in {"SUCCESS", "DEGRADED"}:
        errors.append("Agent04 decision state failed or has unknown health")
    else:
        fresh, reason, age = validate_state_freshness(decision_state, AGENT04_MAX_AGE_SECONDS, now=now)
        freshness = {"fresh": fresh, "reason": reason, "age_seconds": age, "max_age_seconds": AGENT04_MAX_AGE_SECONDS}
        if not fresh:
            errors.append(f"Agent04 decision state rejected: {reason}")

    if errors:
        result = {"permission": "BLOCK_TRADING", "reason": "; ".join(errors)}
        return result, "FAILED", errors, freshness

    decision = decision_state.get("data", {})
    result = PermissionEngine().evaluate(decision)

    if result["permission"] == "BLOCK_TRADING":
        status = "DEGRADED"
    elif decision_state.get("status") == "DEGRADED":
        result = {
            "permission": "CAUTION",
            "reason": "Agent04 is degraded; human review required.",
        }
        status = "DEGRADED"
    else:
        status = "SUCCESS"

    return result, status, errors, freshness


def main():
    decision_state = read_state("decision.json")
    data, status, errors, freshness = build_permission(decision_state)
    write_state(
        agent="Agent05",
        version="0.2",
        filename="permission.json",
        data=data,
        status=status,
        errors=errors,
        metadata={"input": "decision.json", "policy": "fail-closed", "freshness": freshness},
    )
    print(f"Agent05 health: {status} | Permission: {data['permission']}")
    if status == "FAILED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
