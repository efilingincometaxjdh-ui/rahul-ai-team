import unittest

from agent04 import build_decision
from agent05 import build_permission
from decision.engine import DecisionEngine
from permissions.engine import PermissionEngine


class DecisionEngineTests(unittest.TestCase):
    def test_extreme_risk_blocks_decision(self):
        result = DecisionEngine().evaluate(
            {"gold_bias": "BULLISH", "news_risk": "EXTREME"},
            {"trend": "Bullish", "ema20": 2, "ema50": 1, "adx": 30, "rsi": 50},
        )
        self.assertEqual(result["decision"], "NO_TRADE")

    def test_bullish_alignment(self):
        result = DecisionEngine().evaluate(
            {"gold_bias": "BULLISH", "news_risk": "LOW"},
            {"trend": "Bullish", "ema20": 2, "ema50": 1, "adx": 30, "rsi": 50},
        )
        self.assertEqual(result["decision"], "STRONG_BULLISH")


class Agent04Tests(unittest.TestCase):
    def test_missing_upstream_fails_closed(self):
        result, status, errors, _ = build_decision(None, None)
        self.assertEqual(status, "FAILED")
        self.assertEqual(result["decision"], "NO_TRADE")
        self.assertTrue(errors)

    def test_uses_h1_before_lower_timeframes(self):
        technical = {
            "M5": {"trend": "Bearish", "ema20": 1, "ema50": 2, "adx": 30, "rsi": 50},
            "H1": {"trend": "Bullish", "ema20": 2, "ema50": 1, "adx": 30, "rsi": 50},
        }
        a2 = {"status": "SUCCESS", "data": technical}
        a3 = {"status": "SUCCESS", "data": {"gold_bias": "BULLISH", "high_impact_count": 0}}
        result, status, _, metadata = build_decision(a2, a3)
        self.assertEqual(status, "SUCCESS")
        self.assertEqual(metadata["technical_timeframe"], "H1")
        self.assertEqual(result["decision"], "STRONG_BULLISH")


class PermissionEngineTests(unittest.TestCase):
    def test_no_trade_blocks(self):
        result = PermissionEngine().evaluate({"decision": "NO_TRADE", "confidence": 100, "risk": "EXTREME"})
        self.assertEqual(result["permission"], "BLOCK_TRADING")

    def test_low_confidence_is_caution(self):
        result = PermissionEngine().evaluate({"decision": "BULLISH", "confidence": 40, "risk": "LOW"})
        self.assertEqual(result["permission"], "CAUTION")


class Agent05Tests(unittest.TestCase):
    def test_missing_decision_fails_closed(self):
        result, status, errors = build_permission(None)
        self.assertEqual(status, "FAILED")
        self.assertEqual(result["permission"], "BLOCK_TRADING")
        self.assertTrue(errors)

    def test_degraded_decision_never_grants_authority(self):
        state = {
            "status": "DEGRADED",
            "data": {"decision": "BULLISH", "confidence": 80, "risk": "LOW"},
        }
        result, status, _ = build_permission(state)
        self.assertEqual(status, "DEGRADED")
        self.assertEqual(result["permission"], "CAUTION")


if __name__ == "__main__":
    unittest.main()
