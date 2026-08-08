"""Deterministic, evidence-only replay of validated historical XAUUSD candles.

Replay never fetches data, writes repository state, calls Agent04/05/06, or
creates execution authority. The complete persisted dataset is validated before
any replay callback is invoked so malformed, duplicate, or out-of-order history
cannot produce a partial replay.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List

from market.historical import validate_candle


def load_replay_candles(path: str | Path) -> List[Dict]:
    """Validate and return historical candles in persisted chronological order."""
    source = Path(path)
    if not source.exists():
        return []

    candles: List[Dict] = []
    previous_timestamp = None
    seen = set()

    with source.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = validate_candle(json.loads(line))
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                raise ValueError(f"invalid replay record at line {line_number}") from exc

            timestamp = record["datetime"]
            if timestamp in seen:
                raise ValueError(f"duplicate replay timestamp at line {line_number}")
            if previous_timestamp is not None and timestamp <= previous_timestamp:
                raise ValueError(f"replay history is not strictly chronological at line {line_number}")

            seen.add(timestamp)
            previous_timestamp = timestamp
            candles.append(record)

    return candles


def replay_candles(path: str | Path, on_candle: Callable[[int, Dict], None]) -> int:
    """Replay a fully validated candle dataset exactly once in chronological order."""
    if not callable(on_candle):
        raise TypeError("on_candle must be callable")

    candles = load_replay_candles(path)
    for sequence, candle in enumerate(candles):
        on_candle(sequence, dict(candle))
    return len(candles)
