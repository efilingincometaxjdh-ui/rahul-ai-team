"""market/provider.py

IMarketDataProvider interface and a TwelveDataProvider HTTP client.

The provider reuses the existing Twelve Data integration boundary used by
Agent02. It uses only Python's standard library for transport so the provider
module remains importable in the deterministic CI environment without adding a
runtime dependency. A small injectable session hook keeps HTTP behavior easy to
mock in tests.
"""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class IMarketDataProvider(ABC):
    """Abstract market data provider interface."""

    @abstractmethod
    def fetch_candles(self, label: str, interval: str) -> List[Dict]:
        raise NotImplementedError


class TwelveDataProvider(IMarketDataProvider):
    """Twelve Data HTTP client implementation for XAU/USD candles."""

    BASE_URL = "https://api.twelvedata.com/time_series"

    def __init__(self, api_key: Optional[str] = None, session=None):
        self.api_key = api_key or os.environ.get("TWELVE_DATA_API_KEY")
        self.session = session

    @staticmethod
    def _ensure_utc_iso(dt_str: str) -> str:
        if not isinstance(dt_str, str) or not dt_str:
            raise ValueError("invalid datetime")
        if dt_str.endswith("Z"):
            dt = datetime.fromisoformat(dt_str[:-1] + "+00:00")
        else:
            try:
                dt = datetime.fromisoformat(dt_str)
            except ValueError:
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()

    def _get_json(self, params: Dict) -> Dict:
        if self.session is not None:
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            if response.status_code != 200:
                raise RuntimeError(f"TwelveData HTTP error: {response.status_code}")
            return response.json()

        query = urlencode(params)
        request = Request(f"{self.BASE_URL}?{query}", method="GET")
        try:
            with urlopen(request, timeout=10) as response:
                if response.status != 200:
                    raise RuntimeError(f"TwelveData HTTP error: {response.status}")
                return json.loads(response.read().decode("utf-8"))
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(f"TwelveData request failed: {exc}") from exc

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
        data = self._get_json(params)
        if not isinstance(data, dict) or data.get("status") == "error" or "values" not in data:
            raise RuntimeError(f"TwelveData returned unexpected payload: {data}")

        candles: List[Dict] = []
        for item in reversed(data.get("values", [])):
            if not isinstance(item, dict):
                continue
            dt = item.get("datetime") or item.get("timestamp") or item.get("date")
            if not dt:
                continue
            try:
                candle = {
                    "datetime": self._ensure_utc_iso(dt),
                    "open": float(item["open"]),
                    "high": float(item["high"]),
                    "low": float(item["low"]),
                    "close": float(item["close"]),
                }
            except (KeyError, TypeError, ValueError):
                continue
            candles.append(candle)
        return candles
