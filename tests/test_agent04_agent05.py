import unittest

from agent04 import build_decision, fuse_technical_state
from agent05 import build_permission
from decision.engine import DecisionEngine
from permissions.engine import PermissionEngine


def tech(trend, ema20, ema50, adx=30, rsi=50):
    return {"trend": trend, "ema20": ema20, "ema50": ema50, "adx": adx, "rsi": rsi}


class DecisionEngineTests(unittest.TestCase):
    def test_extreme_risk_blocks_decision(self):
        result = DecisionEngine().evaluate(
            {"gold_bias": "BULLISH", "news_risk": "EXTREME"}, tech("Bullish", 2, 1)
        )
        self.assertEqual(result["decision"], "NO_TRADE")

    def test_bullish_alignment(self):
        result = DecisionEngine().evaluate(
            {"gold_bias": "BULLISH", "news_risk": "LOW"}, tech("Bullish", 2, 1)
        )
        self.assertEqual(result["decision"], "STRONG_BULLISH")


class Agent04FusionTests(unittest.TestCase):
    def test_missing_upstream_fails_closed(self):
        result, status, errors, _ = build_decision(None, None)
        self.assertEqual(status, "FAILED")
        self.assertEqual(result["decision"], "NO_TRADE")
        self.assertTrue(errors)

    def test_higher_timeframes_outvote_lower_timeframes(self):
        a2 = {
            "status": "SUCCESS",
            "data": {
                "H4": tech("Bullish", 2050, 2040),
                "H1": tech("Bullish", 2048, 2041),
                "M15": tech("Bearish", 2038, 2042),
                "M5": tech("Bearish", 2037, 2043),
            },
        }
        fused, metadata = fuse_technical_state(a2)
        self.assertEqual(fused["trend"], "Bullish")
        self.assertEqual(metadata["trend_votes"], {"bullish": 7, "bearish": 3})
        self.assertEqual(set(metadata["usable_timeframes"]), {"H4", "H1", "M15", "M5"})

    def test_incomplete_timeframe_is_excluded(self):
        a2 = {
            "status": "SUCCESS",
            "data": {
                "H4": tech("Bullish", 2050, 2040),
                "H1": {"trend": "Bearish", "ema20": 1},
            },
        }
        fused, metadata = fuse_technical_state(a2)
        self.assertEqual(fused["trend"], "Bullish")
        self.assertEqual(metadata["usable_timeframes"], ["H4"])

    def test_no_complete_timeframe_fails_closed(self):
        a2 = {"status": "SUCCESS", "data": {"H1": {"trend": "Bullish"}}}
        a3 = {"status": "SUCCESS", "data": {"gold_bias": "BULLISH", "high_impact_count": 0}}
        result, status, errors, _ = build_decision(a2, a3)
        self.assertEqual(status, "FAILED")
        self.assertEqual(result["decision"], "NO_TRADE")
        self.assertIn("No complete technical timeframe available", errors)

    def test_degraded_upstream_marks_decision_degraded(self):
        a2 = {"status": "DEGRADED", "data": {"H4": tech("Bullish", 2, 1)}}
        a3 = {"status": "SUCCESS", "data": {"gold_bias": "BULLISH", "high_impact_count": 0}}
        result, status, _, _ = build_decision(a2, a3)
        self.assertEqual(status, "DEGRADED")
        self.assertNotEqual(result["decision"], "NO_TRADE")


class PermissionEngineTests(unittest.TestCase):
    def test_no_trade_blocks(self):
        result = PermissionEngine().evaluate({"decision": "NO_TRADE", "confidence": 100, "risk": "EXTREME"})
        self.assertEqual(result["permission"], "BLOCK_TRADING")

    def test_invalid_input_blocks(self):
        self.assertEqual(PermissionEngine().evaluate(None)["permission"], "BLOCK_TRADING")

    def test_unknown_state_blocks(self):
        result = PermissionEngine().evaluate({"decision": "UNKNOWN", "confidence": 90, "risk": "LOW"})
        self.assertEqual(result["permission"], "BLOCK_TRADING")

    def test_unknown_risk_blocks(self):
        result = PermissionEngine().evaluate({"decision": "BULLISH", "confidence": 90, "risk": "UNKNOWN"})
        self.assertEqual(result["permission"], "BLOCK_TRADING")

    def test_invalid_confidence_blocks(self):
        result = PermissionEngine().evaluate({"decision": "BULLISH", "confidence": 101, "risk": "LOW"})
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
