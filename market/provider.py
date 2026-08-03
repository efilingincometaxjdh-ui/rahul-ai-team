"""market/provider.py

IMarketDataProvider interface and a TwelveDataProvider HTTP client.

TwelveDataProvider uses the Twelve Data time_series endpoint. When the
TWELVE_DATA_API_KEY is missing the provider raises RuntimeError (backwards
compatible). Network requests use the requests library and are safe to mock in
unit tests by patching requests.get.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime, timezone

import requests


class IMarketDataProvider(ABC):
    """Abstract market data provider interface.

    Implementations must return a list of candle dictionaries sorted ascending
    by datetime. Each candle must contain at least the keys: open, high, low,
    close and datetime (ISO-8601 timezone-aware string).
    """

    @abstractmethod
    def fetch_candles(self, label: str, interval: str) -> List[Dict]:
        raise NotImplementedError


class TwelveDataProvider(IMarketDataProvider):
    """Twelve Data HTTP client implementation.

    Configuration: TWELVE_DATA_API_KEY environment variable or api_key argument.

    This client calls the `time_series` endpoint and converts provider data to
    the canonical candle format required by the rest of the system. The method
    will raise RuntimeError when the API key is not configured.
    """

    BASE_URL = "https://api.twelvedata.com/time_series"

    def __init__(self, api_key: Optional[str] = None, session: Optional[requests.Session] = None):
        self.api_key = api_key or os.environ.get("TWELVE_DATA_API_KEY")
        self.session = session or requests.Session()

    @staticmethod
    def _ensure_utc_iso(dt_str: str) -> str:
        # Accept ISO strings with or without timezone. Normalize to UTC ISO-8601.
        if dt_str.endswith("Z"):
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        else:
            try:
                dt = datetime.fromisoformat(dt_str)
            except Exception:
                # Fallback: try parsing without microseconds
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                dt = dt.replace(tzinfo=timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()

    def fetch_candles(self, label: str, interval: str) -> List[Dict]:
        if not self.api_key:
            raise RuntimeError("TWELVE_DATA_API_KEY missing")

        params = {
            "symbol": "XAU/USD",
            "interval": interval,
            "format": "JSON",
            "outputsize": 5000,
            "apikey": self.api_key,
        }

        resp = self.session.get(self.BASE_URL, params=params, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"TwelveData HTTP error: {resp.status_code}")

        data = resp.json()
        # Twelve Data returns an error key when something goes wrong
        if not isinstance(data, dict) or data.get("status") == "error" or "values" not in data:
            raise RuntimeError(f"TwelveData returned unexpected payload: {data}")

        values = data.get("values", [])
        candles = []
        # Values are commonly returned newest-first; normalize to ascending
        for item in reversed(values):
            dt = item.get("datetime") or item.get("timestamp") or item.get("date")
            if not dt:
                continue
            dt_iso = self._ensure_utc_iso(dt)
            try:
                open_p = float(item.get("open"))
                high_p = float(item.get("high"))
                low_p = float(item.get("low"))
                close_p = float(item.get("close"))
            except Exception:
                # Skip malformed entries
                continue
            candles.append({
                "datetime": dt_iso,
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close_p,
            })

        return candles
