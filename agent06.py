# RAHUL AI TEAM — AGENT 06: READ-ONLY ALERT GATEWAY

from utils.json_reader import read_state
from utils.json_writer import write_state
from utils.state_validation import validate_state_freshness

AGENT05_MAX_AGE_SECONDS = 15 * 60
SAFE_PERMISSIONS = {"ALLOW_BUYS", "ALLOW_SELLS", "ALLOW_BOTH", "CAUTION", "BLOCK_TRADING"}


def build_alert(permission_state, now=None):
    """Create a read-only alert from Agent 05. This function grants no execution capability."""
    errors = []
    freshness = {"fresh": False, "reason": "not evaluated"}

    if not isinstance(permission_state, dict):
        errors.append("Agent05 permission state missing or malformed")
    elif permission_state.get("status") not in {"SUCCESS", "DEGRADED"}:
        errors.append("Agent05 permission state failed or has unknown health")
    else:
        fresh, reason, age = validate_state_freshness(permission_state, AGENT05_MAX_AGE_SECONDS, now=now)
        freshness = {
            "fresh": fresh,
            "reason": reason,
            "age_seconds": age,
            "max_age_seconds": AGENT05_MAX_AGE_SECONDS,
        }
        if not fresh:
            errors.append(f"Agent05 permission state rejected: {reason}")

    data = permission_state.get("data", {}) if isinstance(permission_state, dict) else {}
    permission = str(data.get("permission", "BLOCK_TRADING")).upper()
    reason = str(data.get("reason", "No safe permission available."))

    if permission not in SAFE_PERMISSIONS:
        errors.append("Agent05 emitted unknown permission")
        permission = "BLOCK_TRADING"
        reason = "Unknown Agent05 permission; alert gateway failed closed."

    if errors:
        return {
            "permission": "BLOCK_TRADING",
            "reason": "; ".join(errors),
            "upstream_health": permission_state.get("status") if isinstance(permission_state, dict) else "MISSING",
            "fresh": False,
            "execution_enabled": False,
        }, "FAILED", errors, freshness

    if permission_state.get("status") == "DEGRADED" and permission not in {"CAUTION", "BLOCK_TRADING"}:
        permission = "CAUTION"
        reason = "Agent05 is degraded; alert downgraded to CAUTION."

    status = "DEGRADED" if permission_state.get("status") == "DEGRADED" or permission in {"CAUTION", "BLOCK_TRADING"} else "SUCCESS"
    return {
        "permission": permission,
        "reason": reason,
        "upstream_health": permission_state.get("status"),
        "fresh": True,
        "execution_enabled": False,
    }, status, errors, freshness


def main():
    permission_state = read_state("permission.json")
    data, status, errors, freshness = build_alert(permission_state)
    write_state(
        agent="Agent06",
        version="0.1",
        filename="alert.json",
        data=data,
        status=status,
        errors=errors,
        metadata={
            "input": "permission.json",
            "freshness": freshness,
            "mode": "read-only",
            "execution_enabled": False,
        },
    )
    print(f"Agent06 health: {status} | Alert: {data['permission']} | Execution: DISABLED")
    if status == "FAILED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
