import unittest

from market.indicators import ema, calculate_indicators
from market.structure import analyze_structure


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


if __name__ == "__main__":
    unittest.main()
