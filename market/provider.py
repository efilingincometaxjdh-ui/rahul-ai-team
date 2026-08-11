"""cTrader Open API market-data provider for Agent 02.

This module is deliberately market-data-only. It can read historical XAUUSD
trend bars from a cTrader account but contains no order/execution operations.
The official Spotware Python SDK is imported lazily so deterministic CI tests
can exercise the provider interface without opening a network connection.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional


class IMarketDataProvider:
    """Small provider contract used by Agent 02 and deterministic tests."""

    def fetch_candles(self, label: str, interval: str) -> List[Dict]:
        raise NotImplementedError


class CTraderOpenAPIProvider(IMarketDataProvider):
    """Read-only XAU/USD historical candles through cTrader Open API.

    Required environment variables:
      CTRADER_CLIENT_ID
      CTRADER_CLIENT_SECRET
      CTRADER_ACCESS_TOKEN

    Optional:
      CTRADER_ACCOUNT_ID  Explicit cTrader account ID. If omitted, the first
                          account granted to the access token is selected.
      CTRADER_ENVIRONMENT=demo|live (default: demo)
      CTRADER_SYMBOL=XAUUSD (broker-specific symbol name is resolved
      case-insensitively with '/' removed)
      CTRADER_HISTORY_COUNT=5000
    """

    PERIODS = {"5min": "M5", "15min": "M15", "1h": "H1", "4h": "H4"}

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        account_id: Optional[str] = None,
        environment: Optional[str] = None,
        symbol_name: Optional[str] = None,
        history_count: Optional[int] = None,
    ):
        self.client_id = client_id or os.environ.get("CTRADER_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("CTRADER_CLIENT_SECRET")
        self.access_token = access_token or os.environ.get("CTRADER_ACCESS_TOKEN")
        self.account_id = account_id or os.environ.get("CTRADER_ACCOUNT_ID")
        self.environment = (environment or os.environ.get("CTRADER_ENVIRONMENT", "demo")).lower()
        self.symbol_name = symbol_name or os.environ.get("CTRADER_SYMBOL", "XAUUSD")
        self.history_count = int(history_count or os.environ.get("CTRADER_HISTORY_COUNT", "5000"))

    @staticmethod
    def _require(value: Optional[str], name: str) -> str:
        if not value:
            raise RuntimeError(f"{name} missing")
        return value

    @staticmethod
    def _normalise_symbol(value: str) -> str:
        return "".join(ch for ch in value.upper() if ch.isalnum())

    @classmethod
    def _period(cls, interval: str):
        try:
            return cls.PERIODS[interval]
        except KeyError as exc:
            raise ValueError(f"unsupported cTrader interval: {interval}") from exc

    @staticmethod
    def _bar_to_candle(bar, digits: int) -> Dict:
        low = float(bar.low) / 100000.0
        open_price = (float(bar.low) + float(getattr(bar, "deltaOpen", 0))) / 100000.0
        close_price = (float(bar.low) + float(getattr(bar, "deltaClose", 0))) / 100000.0
        high_price = (float(bar.low) + float(getattr(bar, "deltaHigh", 0))) / 100000.0
        timestamp = datetime.fromtimestamp(
            int(bar.utcTimestampInMinutes) * 60,
            tz=timezone.utc,
        ).isoformat()
        return {
            "datetime": timestamp,
            "open": round(open_price, digits),
            "high": round(high_price, digits),
            "low": round(low, digits),
            "close": round(close_price, digits),
        }

    def fetch_candles(self, label: str, interval: str) -> List[Dict]:
        return self.fetch_many({label: interval}).get(label, [])

    def fetch_many(self, timeframes: Dict[str, str]) -> Dict[str, List[Dict]]:
        """Fetch all requested timeframes over one authenticated cTrader connection.

        Authentication follows Spotware's required sequence:
        application auth -> account list by access token -> account auth.
        If CTRADER_ACCOUNT_ID is supplied, that account must be among the
        accounts granted to the access token; otherwise the first granted
        account is selected.
        """
        client_id = self._require(self.client_id, "CTRADER_CLIENT_ID")
        client_secret = self._require(self.client_secret, "CTRADER_CLIENT_SECRET")
        access_token = self._require(self.access_token, "CTRADER_ACCESS_TOKEN")
        requested_account_id = int(self.account_id) if self.account_id else None

        try:
            from ctrader_open_api import Client, EndPoints, TcpProtocol
            from ctrader_open_api.messages.OpenApiMessages_pb2 import (
                ProtoOAAccountAuthReq,
                ProtoOAApplicationAuthReq,
                ProtoOAGetAccountListByAccessTokenReq,
                ProtoOAGetTrendbarsReq,
                ProtoOASymbolByIdReq,
                ProtoOASymbolsListReq,
            )
            from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOATrendbarPeriod
            from twisted.internet import reactor
        except ImportError as exc:
            raise RuntimeError(
                "ctrader-open-api is required for runtime market-data collection"
            ) from exc

        if reactor.running:
            raise RuntimeError("cTrader provider cannot start while Twisted reactor is already running")

        host = (
            EndPoints.PROTOBUF_LIVE_HOST
            if self.environment == "live"
            else EndPoints.PROTOBUF_DEMO_HOST
        )
        client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)
        results: Dict[str, List[Dict]] = {}
        failure: List[str] = []
        selected_symbol: Dict[str, int] = {}
        symbol_digits: Dict[str, int] = {}
        pending = {label for label in timeframes}

        def stop():
            try:
                client.stopService()
            finally:
                if reactor.running:
                    reactor.stop()

        def fail(error):
            failure.append(str(error))
            stop()

        def request_symbols(_response):
            request = ProtoOASymbolsListReq()
            request.ctidTraderAccountId = int(self._active_account_id)
            request.includeArchivedSymbols = False
            client.send(request).addCallbacks(on_symbols, fail)

        def send_account_auth(_response):
            request = ProtoOAAccountAuthReq()
            request.ctidTraderAccountId = int(self._active_account_id)
            request.accessToken = access_token
            client.send(request).addCallbacks(request_symbols, fail)

        def on_account_list(response):
            accounts = list(response.ctidTraderAccount)
            if not accounts:
                fail("cTrader access token has no granted trading accounts")
                return

            if requested_account_id is None:
                self._active_account_id = int(accounts[0].ctidTraderAccountId)
            else:
                matches = [
                    account
                    for account in accounts
                    if int(account.ctidTraderAccountId) == requested_account_id
                ]
                if not matches:
                    fail(
                        f"CTRADER_ACCOUNT_ID {requested_account_id} is not granted to the access token"
                    )
                    return
                self._active_account_id = requested_account_id

            send_account_auth(response)

        def on_application_auth(_response):
            request = ProtoOAGetAccountListByAccessTokenReq()
            request.accessToken = access_token
            client.send(request).addCallbacks(on_account_list, fail)

        def on_symbols(response):
            wanted = self._normalise_symbol(self.symbol_name)
            matches = [
                symbol for symbol in response.symbol
                if self._normalise_symbol(symbol.symbolName) == wanted
            ]
            if not matches:
                fail(f"cTrader symbol not found: {self.symbol_name}")
                return
            selected_symbol["id"] = int(matches[0].symbolId)
            request = ProtoOASymbolByIdReq()
            request.ctidTraderAccountId = int(self._active_account_id)
            request.symbolId.append(selected_symbol["id"])
            client.send(request).addCallbacks(on_full_symbol, fail)

        def on_full_symbol(response):
            if not response.symbol:
                fail(f"cTrader returned no full symbol for {self.symbol_name}")
                return
            symbol_digits["digits"] = int(response.symbol[0].digits)
            for label, interval in timeframes.items():
                request = ProtoOAGetTrendbarsReq()
                request.ctidTraderAccountId = int(self._active_account_id)
                request.symbolId = selected_symbol["id"]
                request.period = ProtoOATrendbarPeriod.Value(self._period(interval))
                request.toTimestamp = int(time.time() * 1000)
                request.count = self.history_count
                client.send(request).addCallbacks(
                    lambda response, label=label: on_trendbars(response, label),
                    fail,
                )

        def on_trendbars(response, label):
            digits = symbol_digits["digits"]
            candles = [self._bar_to_candle(bar, digits) for bar in response.trendbar]
            candles.sort(key=lambda candle: candle["datetime"])
            results[label] = candles
            pending.discard(label)
            if not pending:
                stop()

        def connected(_client):
            request = ProtoOAApplicationAuthReq()
            request.clientId = client_id
            request.clientSecret = client_secret
            client.send(request).addCallbacks(on_application_auth, fail)

        client.setConnectedCallback(connected)
        client.setDisconnectedCallback(lambda _client, reason: fail(f"cTrader disconnected: {reason}"))
        client.startService()
        reactor.run()

        if failure:
            raise RuntimeError(failure[0])
        return results
