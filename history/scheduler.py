"""Deterministic Phase 2 observation/outcome scheduling boundary.

This module defines collection timing only. It performs no networking, persistence,
permission evaluation, alert generation, or execution.
"""

from datetime import datetime, timedelta, timezone

from history.observations import HORIZON_DELTAS, HORIZONS

OBSERVATION_INTERVAL = timedelta(minutes=15)


def _parse_timestamp(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include timezone information")
    return parsed.astimezone(timezone.utc)


def observation_slot(value):
    """Return the UTC 15-minute slot containing an aware timestamp."""
    timestamp = _parse_timestamp(value, "timestamp")
    return timestamp.replace(minute=(timestamp.minute // 15) * 15, second=0, microsecond=0)


def is_observation_due(last_observed_at, now):
    """Return whether the current UTC 15-minute slot has not been observed yet.

    A missing last observation is due immediately. This function intentionally
    does not impose a lateness tolerance; that remains an empirical Phase 2 gate.
    """
    current_slot = observation_slot(now)
    if last_observed_at is None:
        return True
    return observation_slot(last_observed_at) < current_slot


def due_horizons(observed_at, now):
    """Return horizons whose minimum measurement time has been reached.

    The result is ordered by horizon duration and does not define a maximum
    lateness window. Reference-price acquisition remains the caller's concern.
    """
    observed = _parse_timestamp(observed_at, "observed_at")
    current = _parse_timestamp(now, "now")
    return tuple(
        horizon
        for horizon in HORIZONS
        if current >= observed + HORIZON_DELTAS[horizon]
    )


def next_observation_slot(value):
    """Return the next UTC 15-minute boundary after an aware timestamp."""
    slot = observation_slot(value)
    return slot + OBSERVATION_INTERVAL
