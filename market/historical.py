"""Evidence-only historical market-data ingestion.

This module persists canonical XAUUSD candles as append-only JSONL. It does not
modify Agent02 current state, Agent04 decisions, Agent05 permissions, or Agent06
alerts. A provider is injected so the existing TwelveDataProvider can be reused
without duplicating transport logic and deterministic tests can use a fake.
"""
from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List


REQUIRED_FIELDS = ("datetime", "open", "high", "low", "close")


def _parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("datetime must be a non-empty ISO-8601 string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return dt


def validate_candle(candle: Dict) -> Dict:
    """Validate and normalize one provider candle for historical storage."""
    if not isinstance(candle, dict):
        raise ValueError("candle must be an object")
    if any(field not in candle for field in REQUIRED_FIELDS):
        raise ValueError("candle missing required field")

    dt = _parse_timestamp(candle["datetime"])
    prices = {}
    for field in ("open", "high", "low", "close"):
        try:
            value = float(candle[field])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field} must be numeric") from exc
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{field} must be finite and positive")
        prices[field] = value

    if prices["high"] < max(prices["open"], prices["close"]):
        raise ValueError("high is below open/close")
    if prices["low"] > min(prices["open"], prices["close"]):
        raise ValueError("low is above open/close")

    return {"datetime": dt.isoformat(), **prices}


def _existing_timestamps(path: Path) -> set[str]:
    if not path.exists():
        return set()
    seen: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                normalized = validate_candle(record)
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"invalid historical record at line {line_number}") from exc
            timestamp = normalized["datetime"]
            if timestamp in seen:
                raise ValueError(f"duplicate historical timestamp at line {line_number}")
            seen.add(timestamp)
    return seen


def append_candles(path: str | Path, candles: Iterable[Dict]) -> int:
    """Append unseen validated candles and return the number appended.

    Existing history is never rewritten. Existing timestamps are idempotently
    skipped; corrupt or duplicate persisted history fails closed before any
    append occurs.
    """
    destination = Path(path)
    existing = _existing_timestamps(destination)
    normalized: List[Dict] = []
    batch_seen: set[str] = set()

    for candle in candles:
        record = validate_candle(candle)
        timestamp = record["datetime"]
        if timestamp in existing or timestamp in batch_seen:
            continue
        batch_seen.add(timestamp)
        normalized.append(record)

    if not normalized:
        return 0

    normalized.sort(key=lambda record: record["datetime"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        for record in normalized:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    return len(normalized)


def ingest_historical_xauusd(provider, interval: str, output_path: str | Path) -> int:
    """Fetch XAU/USD candles from an injected provider and append them to JSONL."""
    candles = provider.fetch_candles("XAU/USD", interval)
    return append_candles(output_path, candles)
