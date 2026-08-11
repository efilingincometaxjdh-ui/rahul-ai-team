"""Read-only Binance public market-data provider.

Binance is a supplemental crypto market-data source. It is deliberately not
used as the XAUUSD reference feed: XAUUSD remains sourced from the selected
cTrader broker account. This module supports public Binance spot symbols such
as BTCUSDT/ETHUSDT without API credentials and performs no trading operations.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class BinancePublicProvider:
    """Fetch public Binance spot prices/candles without credentials."""

    INTERVALS = {"1min": "1m", "5min": "5m", "15min": "15m", "1h": "1h", "4h": "4h"}
    BASE_URL = "https://api.binance.com"

    def __init__(
        self,
        symbol: str = "BTCUSDT",
        base_url: str = BASE_URL,
        http_get: Optional[Callable[[str], bytes]] = None,
    ):
        self.symbol = symbol.upper()
        self.base_url = base_url.rstrip("/")
        self._http_get = http_get or self._default_http_get

    @staticmethod
    def _default_http_get(url: str) -> bytes:
        request = Request(url, headers={"User-Agent": "rahul-ai-team-market-data/1.0"})
        with urlopen(request, timeout=10) as response:
            return response.read()

    @classmethod
    def _interval(cls, interval: str) -> str:
        try:
            return cls.INTERVALS[interval]
        except KeyError as exc:
            raise ValueError(f"unsupported Binance interval: {interval}") from exc

    def fetch_price(self, symbol: Optional[str] = None) -> Dict:
        """Fetch the current public Binance spot ticker for a symbol."""
        requested = (symbol or self.symbol).upper()
        query = urlencode({"symbol": requested})
        payload = json.loads(self._http_get(f"{self.base_url}/api/v3/ticker/price?{query}").decode("utf-8"))
        if not isinstance(payload, dict) or "symbol" not in payload or "price" not in payload:
            raise RuntimeError("invalid Binance ticker response")
        return {
            "symbol": str(payload["symbol"]).upper(),
            "price": float(payload["price"]),
            "source": "binance_spot",
        }

    def fetch_candles(self, label: str, interval: str, limit: int = 500) -> List[Dict]:
        """Fetch normalized public Binance spot klines for one timeframe."""
        if not 1 <= int(limit) <= 1000:
            raise ValueError("Binance candle limit must be between 1 and 1000")
        query = urlencode(
            {
                "symbol": self.symbol,
                "interval": self._interval(interval),
                "limit": int(limit),
            }
        )
        payload = json.loads(self._http_get(f"{self.base_url}/api/v3/klines?{query}").decode("utf-8"))
        if not isinstance(payload, list):
            raise RuntimeError("invalid Binance kline response")

        candles: List[Dict] = []
        for row in payload:
            if not isinstance(row, list) or len(row) < 6:
                raise RuntimeError("malformed Binance kline row")
            timestamp = datetime.fromtimestamp(int(row[0]) / 1000, tz=timezone.utc).isoformat()
            candles.append(
                {
                    "datetime": timestamp,
                    "open": float(row[1]),
                    "high": float(row[2]),
                    "low": float(row[3]),
                    "close": float(row[4]),
                    "volume": float(row[5]),
                    "symbol": self.symbol,
                    "source": "binance_spot",
                    "timeframe": label,
                }
            )
        return candles
