import json
import os
from datetime import datetime, timezone


STATE_DIR = os.path.join("data", "current")


def write_state(agent, version, filename, data, status="SUCCESS", errors=None, metadata=None, state_dir=None):
    """Write an agent state file atomically with explicit health information."""
    state = {
        "agent": agent,
        "version": version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "data": data,
    }

    if errors:
        state["errors"] = errors
    if metadata:
        state["metadata"] = metadata

    target_dir = state_dir or STATE_DIR
    os.makedirs(target_dir, exist_ok=True)

    path = os.path.join(target_dir, filename)
    temp_path = path + ".tmp"

    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(state, file, indent=4)
        file.flush()
        os.fsync(file.fileno())

    os.replace(temp_path, path)
    return state
