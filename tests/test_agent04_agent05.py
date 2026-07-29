import unittest
from datetime import datetime, timedelta, timezone

from agent04 import build_decision, fuse_technical_state
from agent05 import build_permission
from decision.engine import DecisionEngine
from permissions.engine import PermissionEngine

NOW = datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc)


def tech(trend, ema20, ema50, adx=30, rsi=50):
    return {"trend": trend, "ema20": ema20, "ema50": ema50, "adx": adx, "rsi": rsi}


def state(status, data, age_minutes=0):
    return {
        "status": status,
        "generated_at": (NOW - timedelta(minutes=age_minutes)).isoformat(),
        "data": data,
    }


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
        result, status_value, errors, _ = build_decision(None, None, now=NOW)
        self.assertEqual(status_value, "FAILED")
        self.assertEqual(result["decision"], "NO_TRADE")
        self.assertTrue(errors)

    def test_higher_timeframes_outvote_lower_timeframes(self):
        a2 = state("SUCCESS", {
            "H4": tech("Bullish", 2050, 2040), "H1": tech("Bullish", 2048, 2041),
            "M15": tech("Bearish", 2038, 2042), "M5": tech("Bearish", 2037, 2043),
        })
        fused, metadata = fuse_technical_state(a2)
        self.assertEqual(fused["trend"], "Bullish")
        self.assertEqual(metadata["trend_votes"], {"bullish": 7, "bearish": 3})

    def test_incomplete_timeframe_is_excluded(self):
        a2 = state("SUCCESS", {"H4": tech("Bullish", 2050, 2040), "H1": {"trend": "Bearish", "ema20": 1}})
        fused, metadata = fuse_technical_state(a2)
        self.assertEqual(fused["trend"], "Bullish")
        self.assertEqual(metadata["usable_timeframes"], ["H4"])

    def test_stale_technical_state_fails_closed(self):
        a2 = state("SUCCESS", {"H4": tech("Bullish", 2, 1)}, age_minutes=21)
        a3 = state("SUCCESS", {"gold_bias": "BULLISH", "news_risk": "LOW"})
        result, status_value, errors, _ = build_decision(a2, a3, now=NOW)
        self.assertEqual(status_value, "FAILED")
        self.assertEqual(result["decision"], "NO_TRADE")
        self.assertTrue(any("Agent02 state rejected" in error for error in errors))

    def test_stale_macro_state_fails_closed(self):
        a2 = state("SUCCESS", {"H4": tech("Bullish", 2, 1)})
        a3 = state("SUCCESS", {"gold_bias": "BULLISH", "news_risk": "LOW"}, age_minutes=361)
        result, status_value, _, _ = build_decision(a2, a3, now=NOW)
        self.assertEqual(status_value, "FAILED")
        self.assertEqual(result["risk"], "EXTREME")

    def test_degraded_upstream_marks_decision_degraded(self):
        a2 = state("DEGRADED", {"H4": tech("Bullish", 2, 1)})
        a3 = state("SUCCESS", {"gold_bias": "BULLISH", "news_risk": "LOW"})
        result, status_value, _, _ = build_decision(a2, a3, now=NOW)
        self.assertEqual(status_value, "DEGRADED")
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


class PipelineContractTests(unittest.TestCase):
    def test_fresh_bullish_pipeline_can_allow_buys(self):
        a2 = state("SUCCESS", {"H4": tech("Bullish", 2050, 2040), "H1": tech("Bullish", 2049, 2041)})
        a3 = state("SUCCESS", {"gold_bias": "BULLISH", "news_risk": "LOW"})
        decision, decision_health, _, _ = build_decision(a2, a3, now=NOW)
        permission, permission_health, _, _ = build_permission(state(decision_health, decision), now=NOW)
        self.assertEqual(decision["decision"], "STRONG_BULLISH")
        self.assertEqual(permission_health, "SUCCESS")
        self.assertEqual(permission["permission"], "ALLOW_BUYS")

    def test_degraded_pipeline_never_grants_authority(self):
        a2 = state("DEGRADED", {"H4": tech("Bullish", 2050, 2040)})
        a3 = state("SUCCESS", {"gold_bias": "BULLISH", "news_risk": "LOW"})
        decision, decision_health, _, _ = build_decision(a2, a3, now=NOW)
        permission, permission_health, _, _ = build_permission(state(decision_health, decision), now=NOW)
        self.assertEqual(permission_health, "DEGRADED")
        self.assertEqual(permission["permission"], "CAUTION")

    def test_stale_decision_blocks_trading(self):
        decision_state = state("SUCCESS", {"decision": "BULLISH", "confidence": 80, "risk": "LOW"}, age_minutes=16)
        permission, permission_health, errors, _ = build_permission(decision_state, now=NOW)
        self.assertEqual(permission_health, "FAILED")
        self.assertEqual(permission["permission"], "BLOCK_TRADING")
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
