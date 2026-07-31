# RAHUL AI TEAM — SAFE HISTORICAL OUTCOME COLLECTOR

from pathlib import Path

from history.observations import append_outcome, build_outcome
from history.reference_price import validate_reference_quote

DEFAULT_OBSERVATION_PATH = Path("data/history/observations.jsonl")
DEFAULT_OUTCOME_PATH = Path("data/history/outcomes.jsonl")


def collect_outcome(
    observation_id,
    horizon,
    reference_quote,
    observation_path=DEFAULT_OBSERVATION_PATH,
    outcome_path=DEFAULT_OUTCOME_PATH,
):
    """Append one outcome from already-fetched, validated reference evidence.

    This function is deliberately transport-free and evidence-only. It performs no
    network requests or scheduling and cannot alter current trading state. The
    provider timestamp is used as measured_at so local runtime cannot fabricate
    outcome timing.
    """
    quote = validate_reference_quote(reference_quote)
    outcome = build_outcome(
        observation_id,
        horizon,
        quote["price"],
        measured_at=quote["observed_at"],
    )
    appended = append_outcome(outcome_path, outcome, observation_path=observation_path)
    return outcome, appended
