import json
import os
from datetime import datetime, timezone


def write_state(agent, version, filename, data, status="SUCCESS", errors=None, metadata=None):
    """Write an agent state file with explicit health information."""
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

    os.makedirs("data/current", exist_ok=True)

    path = os.path.join("data", "current", filename)
    temp_path = path + ".tmp"

    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(state, file, indent=4)
        file.flush()
        os.fsync(file.fileno())

    os.replace(temp_path, path)
    return state
