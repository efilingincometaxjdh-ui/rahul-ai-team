"""history/downloader.py

Append-only historical XAUUSD downloader using an IMarketDataProvider.

Storage: data/history/market/<TIMEFRAME>.jsonl - one candle JSON per line.
Duplicate prevention: skip candles whose datetime already present in the file.
Timestamps normalized to UTC ISO-8601.

The module is safe to unit-test by injecting a provider whose network calls are
mocked or by passing a FakeProvider.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union

from market.provider import IMarketDataProvider, TwelveDataProvider
from agent02 import TIMEFRAMES


HISTORY_DIR = Path("data") / "history" / "market"


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def _utc_iso(dt_str: str) -> str:
    # Expect an ISO string; normalize to timezone-aware UTC ISO format
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        # Fallback: parse naive datetime
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        dt = dt.replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def append_candles_jsonl(filepath: Path, candles: List[Dict]) -> int:
    """Append candles to filepath JSONL, skipping duplicates by datetime.

    Empty input is a true no-op: it must not create a directory or file.
    Returns number of appended candles.
    """
    filepath = Path(filepath)
    if not candles:
        return 0

    _ensure_dir(filepath.parent)
    existing = set()
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as rf:
            for line in rf:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    existing.add(obj.get("datetime"))
                except Exception:
                    # ignore malformed lines
                    continue

    appended = 0
    # Open file for append and ensure durability
    with open(filepath, "a", encoding="utf-8") as af:
        for candle in candles:
            dt = candle.get("datetime")
            if not dt:
                continue
            if dt in existing:
                continue
            af.write(json.dumps(candle, separators=(",", ":")))
            af.write("\n")
            af.flush()
            try:
                os.fsync(af.fileno())
            except Exception:
                pass
            existing.add(dt)
            appended += 1

    return appended


def download_timeframe(
    provider: Optional[IMarketDataProvider],
    label: str,
    interval: str,
    history_dir: Optional[Union[Path, str]] = None,
) -> int:
    """Download candles for a single timeframe and append to JSONL.

    Returns number of appended candles.
    """
    if provider is None:
        provider = TwelveDataProvider()

    candles = provider.fetch_candles(label, interval)
    # Normalize datetimes to UTC ISO
    normalized = []
    for c in candles:
        dt = c.get("datetime")
        if not dt:
            continue
        try:
            dt_iso = _utc_iso(dt)
        except Exception:
            continue
        try:
            open_p = float(c.get("open"))
            high_p = float(c.get("high"))
            low_p = float(c.get("low"))
            close_p = float(c.get("close"))
        except Exception:
            continue
        normalized.append({
            "datetime": dt_iso,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
        })

    history_dir = Path(history_dir) if history_dir is not None else HISTORY_DIR
    filepath = history_dir / f"{label}.jsonl"
    appended = append_candles_jsonl(filepath, normalized)
    return appended


def download_all(provider: Optional[IMarketDataProvider] = None, history_dir: Optional[Union[Path, str]] = None) -> Dict[str, int]:
    """Download all configured timeframes and append to per-timeframe JSONL.

    Returns a dict mapping timeframe label -> appended count.
    """
    results = {}
    for label, interval in TIMEFRAMES.items():
        try:
            count = download_timeframe(provider, label, interval, history_dir=history_dir)
        except Exception:
            count = 0
        results[label] = count
    return results
