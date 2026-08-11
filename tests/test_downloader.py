import json
import os
import tempfile
import unittest

from history.downloader import download_timeframe


class FakeProvider:
    def __init__(self, candles=None, error=None):
        self.candles = candles or []
        self.error = error

    def fetch_candles(self, label, interval):
        if self.error:
            raise self.error
        return list(self.candles)


class DownloaderTests(unittest.TestCase):
    def test_append_only_and_duplicate_prevention(self):
        candles = [
            {"datetime": "2026-01-01T00:00:00Z", "open": 2000, "high": 2001, "low": 1999, "close": 2000.25},
            {"datetime": "2026-01-01T00:05:00Z", "open": 2000.5, "high": 2001.5, "low": 1999.5, "close": 2000.75},
        ]
        provider = FakeProvider(candles)

        with tempfile.TemporaryDirectory() as td:
            history_dir = os.path.join(td, "market")
            appended = download_timeframe(provider, "M5", "5min", history_dir=history_dir)
            self.assertEqual(appended, 2)
            appended2 = download_timeframe(provider, "M5", "5min", history_dir=history_dir)
            self.assertEqual(appended2, 0)
            path = os.path.join(history_dir, "M5.jsonl")
            with open(path, "r", encoding="utf-8") as f:
                lines = [l for l in f if l.strip()]
            self.assertEqual(len(lines), 2)

    def test_utc_normalization(self):
        candles = [
            {"datetime": "2026-01-01 00:00:00", "open": 2000, "high": 2001, "low": 1999, "close": 2000.25},
            {"datetime": "2026-01-01T00:05:00Z", "open": 2000.5, "high": 2001.5, "low": 1999.5, "close": 2000.75},
        ]
        provider = FakeProvider(list(reversed(candles)))

        with tempfile.TemporaryDirectory() as td:
            history_dir = os.path.join(td, "market")
            appended = download_timeframe(provider, "M5", "5min", history_dir=history_dir)
            self.assertEqual(appended, 2)
            path = os.path.join(history_dir, "M5.jsonl")
            with open(path, "r", encoding="utf-8") as f:
                entries = [json.loads(l) for l in f if l.strip()]
            for entry in entries:
                self.assertTrue(entry["datetime"].endswith("+00:00"))

    def test_provider_failure_raises_and_no_write(self):
        provider = FakeProvider(error=RuntimeError("provider failure"))
        with tempfile.TemporaryDirectory() as td:
            history_dir = os.path.join(td, "market")
            with self.assertRaises(RuntimeError):
                download_timeframe(provider, "M5", "5min", history_dir=history_dir)
            path = os.path.join(history_dir, "M5.jsonl")
            self.assertFalse(os.path.exists(path))

    def test_empty_values_no_write(self):
        provider = FakeProvider([])
        with tempfile.TemporaryDirectory() as td:
            history_dir = os.path.join(td, "market")
            appended = download_timeframe(provider, "M5", "5min", history_dir=history_dir)
            self.assertEqual(appended, 0)
            path = os.path.join(history_dir, "M5.jsonl")
            self.assertFalse(os.path.exists(path))

    def test_malformed_candles_are_skipped(self):
        candles = [
            {"datetime": "2026-01-01T00:00:00Z", "open": "bad", "high": 2001, "low": 1999, "close": 2000},
            {"datetime": "2026-01-01T00:05:00Z", "open": 2000.5, "high": 2001.5, "low": 1999.5, "close": 2000.75},
        ]
        provider = FakeProvider(candles)
        with tempfile.TemporaryDirectory() as td:
            history_dir = os.path.join(td, "market")
            appended = download_timeframe(provider, "M5", "5min", history_dir=history_dir)
            self.assertEqual(appended, 1)


if __name__ == "__main__":
    unittest.main()
