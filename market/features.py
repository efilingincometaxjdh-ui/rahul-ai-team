"""Deterministic, versioned feature extraction over validated XAUUSD candles.

This module is an evidence-only transform. It consumes already validated
historical candles, emits immutable feature records keyed by candle timestamp,
and never invokes providers, agents, permissions, alerts, or execution paths.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, List

from market.historical import validate_candle
from market.indicators import calculate_indicators


FEATURE_SCHEMA_VERSION = 1
FEATURE_TRANSFORM_VERSION = "xauusd_technical_v1"


def _validate_history(candles: Iterable[Dict]) -> List[Dict]:
    normalized: List[Dict] = []
    previous_timestamp = None
    seen = set()
    for index, candle in enumerate(candles):
        try:
            record = validate_candle(candle)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid feature input at index {index}") from exc
        timestamp = record["datetime"]
        if timestamp in seen:
            raise ValueError(f"duplicate feature input timestamp at index {index}")
        if previous_timestamp is not None and timestamp <= previous_timestamp:
            raise ValueError(f"feature input is not strictly chronological at index {index}")
        seen.add(timestamp)
        previous_timestamp = timestamp
        normalized.append(record)
    return normalized


def _finite_or_none(value):
    if value is None:
        return None
    if not math.isfinite(float(value)):
        raise ValueError("feature calculation produced a non-finite value")
    return float(value)


def _trend(indicators: Dict):
    ema20 = indicators["ema20"]
    ema50 = indicators["ema50"]
    if ema20 is None or ema50 is None:
        return None
    if ema20 > ema50:
        return "BULLISH"
    if ema20 < ema50:
        return "BEARISH"
    return "NEUTRAL"


def extract_features(candles: Iterable[Dict]) -> List[Dict]:
    """Extract deterministic per-candle technical evidence features.

    Warm-up rows are retained with null indicator values and ``ready=False``;
    once all configured indicators are available, ``ready=True``. The transform
    version is explicit so downstream analytics can partition incompatible
    feature definitions instead of silently mixing them.
    """
    history = _validate_history(candles)
    features: List[Dict] = []

    for index, candle in enumerate(history):
        prefix = history[: index + 1]
        indicators = calculate_indicators(prefix) if len(prefix) >= 1 else {}
        previous_close = history[index - 1]["close"] if index else None
        price_return_1 = (
            None
            if previous_close is None
            else (candle["close"] - previous_close) / previous_close
        )
        candle_range = candle["high"] - candle["low"]
        body = abs(candle["close"] - candle["open"])
        ready = all(indicators[name] is not None for name in ("ema20", "ema50", "rsi14", "atr14", "adx14"))

        record = {
            "schema_version": FEATURE_SCHEMA_VERSION,
            "transform_version": FEATURE_TRANSFORM_VERSION,
            "datetime": candle["datetime"],
            "symbol": "XAU/USD",
            "close": candle["close"],
            "price_return_1": _finite_or_none(price_return_1),
            "range": _finite_or_none(candle_range),
            "body": _finite_or_none(body),
            "ema20": _finite_or_none(indicators.get("ema20")),
            "ema50": _finite_or_none(indicators.get("ema50")),
            "rsi14": _finite_or_none(indicators.get("rsi14")),
            "atr14": _finite_or_none(indicators.get("atr14")),
            "adx14": _finite_or_none(indicators.get("adx14")),
            "trend": _trend(indicators),
            "ready": ready,
        }
        features.append(record)

    return features
