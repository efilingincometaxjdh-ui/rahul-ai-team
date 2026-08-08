import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from market.historical import append_candles, ingest_historical_xauusd


class FakeProvider:
    def __init__(self, candles):
        self.candles = candles
        self.calls = []

    def fetch_candles(self, label, interval):
        self.calls.append((label, interval))
        return list(self.candles)


class HistoricalMarketTests(unittest.TestCase):
    def _candle(self, minutes, close=2000.0):
        dt = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minutes)
        return {
            "datetime": dt.isoformat(),
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
        }

    def test_ingestion_reuses_provider_and_appends_idempotently(self):
        candles = [self._candle(5), self._candle(0)]
        provider = FakeProvider(candles)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "xauusd" / "m5.jsonl"
            self.assertEqual(ingest_historical_xauusd(provider, "5min", path), 2)
            self.assertEqual(ingest_historical_xauusd(provider, "5min", path), 0)
            self.assertEqual(provider.calls, [("XAU/USD", "5min"), ("XAU/USD", "5min")])
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            self.assertLess(json.loads(lines[0])["datetime"], json.loads(lines[1])["datetime"])

    def test_corrupt_existing_history_fails_closed_before_append(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.jsonl"
            path.write_text('{"datetime":"not-a-date"}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                append_candles(path, [self._candle(0)])
            self.assertEqual(path.read_text(encoding="utf-8"), '{"datetime":"not-a-date"}\n')

    def test_duplicate_timestamps_in_existing_history_fail_closed(self):
        candle = self._candle(0)
        line = json.dumps(candle, sort_keys=True, separators=(",", ":"))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.jsonl"
            path.write_text(line + "\n" + line + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                append_candles(path, [self._candle(5)])

    def test_invalid_candle_is_rejected_without_creating_history(self):
        invalid = self._candle(0)
        invalid["close"] = -1
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "history.jsonl"
            with self.assertRaises(ValueError):
                append_candles(path, [invalid])
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
