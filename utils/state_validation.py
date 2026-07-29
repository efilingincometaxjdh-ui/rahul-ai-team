from datetime import datetime, timezone


def parse_generated_at(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def validate_state_freshness(state, max_age_seconds, now=None):
    """Return (is_fresh, reason, age_seconds) for a normalized state envelope."""
    if not isinstance(state, dict):
        return False, "state is missing or malformed", None

    generated_at = parse_generated_at(state.get("generated_at"))
    if generated_at is None:
        return False, "generated_at is missing or invalid", None

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    else:
        current = current.astimezone(timezone.utc)

    age_seconds = (current - generated_at).total_seconds()
    if age_seconds < -60:
        return False, "generated_at is unexpectedly in the future", age_seconds
    if age_seconds > max_age_seconds:
        return False, f"state is stale ({int(age_seconds)}s > {max_age_seconds}s)", age_seconds
    return True, "fresh", max(0.0, age_seconds)
