import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from market.replay import load_replay_candles, replay_candles


class ReplayTests(unittest.TestCase):
    def _candle(self, minutes, close=2000.0):
        dt = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minutes)
        return (
            '{"datetime":"%s","open":%s,"high":%s,"low":%s,"close":%s}'
            % (dt.isoformat(), close, close + 1, close - 1, close)
        )

    def test_replay_is_chronological_and_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m5.jsonl"
            path.write_text(self._candle(0) + "\n" + self._candle(5) + "\n", encoding="utf-8")
            events = []
            count = replay_candles(path, lambda sequence, candle: events.append((sequence, candle["datetime"])))
            self.assertEqual(2, count)
            self.assertEqual([(0, "2026-01-01T00:00:00+00:00"), (1, "2026-01-01T00:05:00+00:00")], events)

    def test_malformed_history_fails_before_any_callback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m5.jsonl"
            path.write_text(self._candle(0) + "\nnot-json\n", encoding="utf-8")
            events = []
            with self.assertRaises(ValueError):
                replay_candles(path, lambda sequence, candle: events.append(sequence))
            self.assertEqual([], events)

    def test_out_of_order_history_fails_before_any_callback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m5.jsonl"
            path.write_text(self._candle(5) + "\n" + self._candle(0) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_replay_candles(path)

    def test_missing_history_is_empty_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.jsonl"
            self.assertEqual([], load_replay_candles(path))
            self.assertEqual(0, replay_candles(path, lambda sequence, candle: None))

    def test_callback_must_be_callable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "m5.jsonl"
            with self.assertRaises(TypeError):
                replay_candles(path, None)


if __name__ == "__main__":
    unittest.main()
