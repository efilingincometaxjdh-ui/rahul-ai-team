import unittest

from market.features import (
    FEATURE_SCHEMA_VERSION,
    FEATURE_TRANSFORM_VERSION,
    extract_features,
)


def candles(count=55):
    rows = []
    for index in range(count):
        base = 2000.0 + index
        rows.append(
            {
                "datetime": f"2026-01-01T00:{index:02d}:00+00:00",
                "open": base,
                "high": base + 2.0,
                "low": base - 1.0,
                "close": base + 1.0,
            }
        )
    return rows


class FeatureExtractionTests(unittest.TestCase):
    def test_empty_history_is_deterministic(self):
        self.assertEqual(extract_features([]), [])

    def test_versioned_warmup_and_ready_features(self):
        result = extract_features(candles())
        self.assertEqual(len(result), 55)
        self.assertEqual(result[0]["schema_version"], FEATURE_SCHEMA_VERSION)
        self.assertEqual(result[0]["transform_version"], FEATURE_TRANSFORM_VERSION)
        self.assertFalse(result[0]["ready"])
        self.assertIsNone(result[0]["ema20"])
        self.assertTrue(result[-1]["ready"])
        self.assertEqual(result[-1]["trend"], "BULLISH")
        self.assertIsNotNone(result[-1]["ema50"])
        self.assertIsNotNone(result[-1]["adx14"])

    def test_same_input_produces_identical_output(self):
        history = candles()
        self.assertEqual(extract_features(history), extract_features(history))

    def test_duplicate_or_out_of_order_history_fails_closed(self):
        history = candles(3)
        with self.assertRaises(ValueError):
            extract_features([history[0], history[0], history[2]])
        with self.assertRaises(ValueError):
            extract_features([history[1], history[0]])

    def test_invalid_price_fails_before_feature_output(self):
        history = candles(2)
        history[1]["close"] = -1
        with self.assertRaises(ValueError):
            extract_features(history)


if __name__ == "__main__":
    unittest.main()
