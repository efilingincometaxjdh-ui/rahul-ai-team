"""Deterministic timing-evidence records for Phase 2 observation cadence."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA_VERSION = "phase2-timing-v1"
CADENCE_MINUTES = 15


def parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("timestamp must be a non-empty ISO-8601 string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def floor_observation_slot(value: str) -> str:
    dt = parse_utc(value)
    minute = (dt.minute // CADENCE_MINUTES) * CADENCE_MINUTES
    slot = dt.replace(minute=minute, second=0, microsecond=0)
    return slot.isoformat().replace("+00:00", "Z")


def build_timing_record(
    *,
    run_id: str,
    workflow_started_at: str,
    workflow_finished_at: str,
    latest_reference_at: str,
) -> dict:
    if not run_id:
        raise ValueError("run_id must be provided")

    started = parse_utc(workflow_started_at)
    finished = parse_utc(workflow_finished_at)
    reference = parse_utc(latest_reference_at)
    if finished < started:
        raise ValueError("workflow_finished_at must not precede workflow_started_at")
    if reference > finished:
        raise ValueError("latest_reference_at must not be future-dated")

    slot = parse_utc(floor_observation_slot(workflow_started_at))
    scheduler_delay = (started - slot).total_seconds()
    reference_age = (finished - reference).total_seconds()

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": str(run_id),
        "cadence_minutes": CADENCE_MINUTES,
        "observation_slot": slot.isoformat().replace("+00:00", "Z"),
        "workflow_started_at": started.isoformat().replace("+00:00", "Z"),
        "workflow_finished_at": finished.isoformat().replace("+00:00", "Z"),
        "latest_reference_at": reference.isoformat().replace("+00:00", "Z"),
        "scheduler_delay_seconds": scheduler_delay,
        "reference_age_seconds": reference_age,
    }


def append_timing_record(path: str | Path, record: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def write_timing_record(
    path: str | Path,
    *,
    run_id: str,
    workflow_started_at: str,
    workflow_finished_at: str,
    latest_reference_at: str,
) -> dict:
    record = build_timing_record(
        run_id=run_id,
        workflow_started_at=workflow_started_at,
        workflow_finished_at=workflow_finished_at,
        latest_reference_at=latest_reference_at,
    )
    append_timing_record(path, record)
    return record
