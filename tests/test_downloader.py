import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from datetime import datetime, timezone

from history.downloader import download_timeframe, append_candles_jsonl, HISTORY_DIR
from market.provider import TwelveDataProvider


class MockResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class MockSession:
    def __init__(self, response):
        self._response = response
        self.last_request = None

    def get(self, url, params=None, timeout=None):
        self.last_request = SimpleNamespace(url=url, params=params, timeout=timeout)
        return self._response


def make_values(start_iso, count, interval_minutes=5):
    # produce newest-first as TwelveData often returns
    values = []
    dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    for i in range(count):
        t = dt.replace(tzinfo=timezone.utc)  # ensure tz-aware
        iso = t.isoformat()
        base = 2000.0 + i * 0.5
        values.insert(0, {"datetime": iso, "open": str(base), "high": str(base + 1), "low": str(base - 1), "close": str(base + 0.25)})
        dt = dt + timedelta(minutes=interval_minutes)
    return values


from datetime import timedelta


class DownloaderTests(unittest.TestCase):
    def test_append_only_and_duplicate_prevention(self):
        # Mock TwelveData response with two candles
        values = [
            {"datetime": "2026-01-01T00:00:00Z", "open": "2000", "high": "2001", "low": "1999", "close": "2000.25"},
            {"datetime": "2026-01-01T00:05:00Z", "open": "2000.5", "high": "2001.5", "low": "1999.5", "close": "2000.75"},
        ]
        resp = MockResponse(200, {"values": values})
        session = MockSession(resp)
        provider = TwelveDataProvider(api_key="key", session=session)

        with tempfile.TemporaryDirectory() as td:
            history_dir = os.path.join(td, "market")
            appended = download_timeframe(provider, "M5", "5min", history_dir=history_dir)
            self.assertEqual(appended, 2)
            # second run should append zero due to duplicates
            appended2 = download_timeframe(provider, "M5", "5min", history_dir=history_dir)
            self.assertEqual(appended2, 0)
            # file should exist and have 2 lines
            path = os.path.join(history_dir, "M5.jsonl")
            with open(path, "r", encoding="utf-8") as f:
                lines = [l for l in f if l.strip()]
            self.assertEqual(len(lines), 2)

    def test_utc_normalization(self):
        # Use mixed datetime formats
        values = [
            {"datetime": "2026-01-01 00:00:00", "open": "2000", "high": "2001", "low": "1999", "close": "2000.25"},
            {"datetime": "2026-01-01T00:05:00Z", "open": "2000.5", "high": "2001.5", "low": "1999.5", "close": "2000.75"},
        ]
        resp = MockResponse(200, {"values": list(reversed(values))})
        session = MockSession(resp)
        provider = TwelveDataProvider(api_key="key", session=session)

        with tempfile.TemporaryDirectory() as td:
            history_dir = os.path.join(td, "market")
            appended = download_timeframe(provider, "M5", "5min", history_dir=history_dir)
            self.assertEqual(appended, 2)
            path = os.path.join(history_dir, "M5.jsonl")
            with open(path, "r", encoding="utf-8") as f:
                entries = [json.loads(l) for l in f if l.strip()]
            for e in entries:
                # all stored datetimes must be timezone-aware UTC
                self.assertTrue(e["datetime"].endswith("+00:00"))

    def test_malformed_response_raises_and_no_write(self):
        # Missing 'values' key
        resp = MockResponse(200, {"foo": "bar"})
        session = MockSession(resp)
        provider = TwelveDataProvider(api_key="key", session=session)
        with tempfile.TemporaryDirectory() as td:
            history_dir = os.path.join(td, "market")
            with self.assertRaises(RuntimeError):
                download_timeframe(provider, "M5", "5min", history_dir=history_dir)
            # file must not exist
            path = os.path.join(history_dir, "M5.jsonl")
            self.assertFalse(os.path.exists(path))

    def test_empty_values_no_write(self):
        resp = MockResponse(200, {"values": []})
        session = MockSession(resp)
        provider = TwelveDataProvider(api_key="key", session=session)
        with tempfile.TemporaryDirectory() as td:
            history_dir = os.path.join(td, "market")
            appended = download_timeframe(provider, "M5", "5min", history_dir=history_dir)
            self.assertEqual(appended, 0)
            path = os.path.join(history_dir, "M5.jsonl")
            self.assertFalse(os.path.exists(path))

    def test_http_failure_raises_and_no_write(self):
        resp = MockResponse(500, {"message": "server error"})
        session = MockSession(resp)
        provider = TwelveDataProvider(api_key="key", session=session)
        with tempfile.TemporaryDirectory() as td:
            history_dir = os.path.join(td, "market")
            with self.assertRaises(RuntimeError):
                download_timeframe(provider, "M5", "5min", history_dir=history_dir)
            path = os.path.join(history_dir, "M5.jsonl")
            self.assertFalse(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
