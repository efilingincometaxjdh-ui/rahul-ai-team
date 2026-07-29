import json
import os
import tempfile
import unittest
from unittest.mock import patch

from agent02 import build_market_state
from market.indicators import ema, calculate_indicators
from market.structure import analyze_structure
from utils.json_reader import read_state
from utils.json_writer import write_state


def make_candles(count=100):
    candles = []
    for i in range(count):
        base = 2000.0 + (i * 0.5)
        candles.append({
            "datetime": f"2026-01-01T00:{i:02d}:00",
            "open": base,
            "high": base + 1.0,
            "low": base - 1.0,
            "close": base + 0.25,
        })
    return candles


class IndicatorTests(unittest.TestCase):
    def test_ema_returns_value(self):
        value = ema(list(range(1, 51)), 20)
        self.assertIsNotNone(value)
        self.assertGreater(value, 0)

    def test_complete_indicator_set(self):
        result = calculate_indicators(make_candles())
        for key in ("ema20", "ema50", "rsi14", "atr14", "adx14"):
            self.assertIn(key, result)
            self.assertIsNotNone(result[key])


class StructureTests(unittest.TestCase):
    def test_uptrend_is_bullish(self):
        result = analyze_structure(make_candles())
        self.assertEqual(result["trend"], "Bullish")
        self.assertLessEqual(result["support"], result["resistance"])

    def test_detects_confirmed_swings(self):
        candles = make_candles(40)
        candles[30]["high"] = 2100.0
        candles[31]["low"] = 1980.0
        result = analyze_structure(candles)
        self.assertEqual(result["swing_high"], 2100.0)
        self.assertEqual(result["swing_low"], 1980.0)


class AgentHealthTests(unittest.TestCase):
    def test_partial_data_is_degraded(self):
        market_data = {
            "M5": make_candles(),
            "M15": make_candles(),
            "H1": None,
            "H4": make_candles(),
        }
        state, status, errors, metadata = build_market_state(market_data)
        self.assertEqual(status, "DEGRADED")
        self.assertNotIn("H1", state)
        self.assertIn("H1", metadata["missing_timeframes"])
        self.assertTrue(errors)

    def test_no_data_is_failed(self):
        state, status, errors, _ = build_market_state({key: None for key in ("M5", "M15", "H1", "H4")})
        self.assertEqual(status, "FAILED")
        self.assertEqual(state, {})
        self.assertEqual(len(errors), 4)


class StateIOTests(unittest.TestCase):
    def test_write_and_read_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("utils.json_writer.os.path.join", side_effect=lambda *parts: os.path.join(temp_dir, parts[-1])):
                written = write_state("TestAgent", "1.0", "state.json", {"ok": True}, status="DEGRADED", errors=["sample"])
                path = os.path.join(temp_dir, "state.json")
                with open(path, "r", encoding="utf-8") as file:
                    stored = json.load(file)
                self.assertEqual(stored["status"], "DEGRADED")
                self.assertEqual(written["errors"], ["sample"])

    def test_reader_missing_optional_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("utils.json_reader.os.path.join", side_effect=lambda *parts: os.path.join(temp_dir, parts[-1])):
                self.assertIsNone(read_state("missing.json"))


if __name__ == "__main__":
    unittest.main()
