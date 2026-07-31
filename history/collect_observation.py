# RAHUL AI TEAM — SAFE HISTORICAL OBSERVATION COLLECTOR

from pathlib import Path

from history.observations import append_observation, build_observation
from utils.json_reader import read_state


DEFAULT_OBSERVATION_PATH = Path("data/history/observations.jsonl")


def collect_observation(trader_view_state, observation_path=DEFAULT_OBSERVATION_PATH, observed_at=None):
    """Append evidence from a normalized TraderView state envelope only.

    This collector is evidence-only. It never writes current agent state, changes
    permission, or enables execution. Invalid/failed TraderView state is rejected.
    """
    if not isinstance(trader_view_state, dict):
        raise ValueError("TraderView state must be a dictionary")
    health = trader_view_state.get("health", {})
    if not isinstance(health, dict) or health.get("status") not in {"SUCCESS", "DEGRADED"}:
        raise ValueError("TraderView state health must be SUCCESS or DEGRADED")
    data = trader_view_state.get("data")
    if not isinstance(data, dict):
        raise ValueError("TraderView state data must be a dictionary")

    observation = build_observation(data, observed_at=observed_at)
    appended = append_observation(observation_path, observation)
    return observation, appended


def main():
    state = read_state("trader_view.json", required=True)
    observation, appended = collect_observation(state)
    action = "APPENDED" if appended else "ALREADY_PRESENT"
    print(f"Historical observation {action}: {observation['observation_id']} | execution authority unchanged")


if __name__ == "__main__":
    main()
