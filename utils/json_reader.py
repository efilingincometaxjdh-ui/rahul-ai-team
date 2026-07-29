import json
import os


STATE_DIR = os.path.join("data", "current")


def read_state(filename, required=False, state_dir=None):
    """Read an agent state and return None when an optional state is missing."""
    path = os.path.join(state_dir or STATE_DIR, filename)

    if not os.path.exists(path):
        if required:
            raise FileNotFoundError(f"State file not found: {path}")
        return None

    try:
        with open(path, "r", encoding="utf-8") as file:
            state = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON state file: {path}") from error

    if not isinstance(state, dict):
        raise ValueError(f"State file must contain a JSON object: {path}")

    return state
