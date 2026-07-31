import unittest

from trader_view import build_trader_view


class TraderViewTests(unittest.TestCase):
    def test_read_only_view_exposes_decision_and_permission(self):
        alert = {"data": {"permission": "ALLOW_BUYS", "reason": "Safe buy permission", "fresh": True, "execution_enabled": False}}
        decision = {
            "data": {"decision": "BUY", "confidence": 82, "risk": "LOW", "reasons": ["Technical and macro aligned"]},
            "metadata": {"technical_fusion": {
                "usable_timeframes": ["H4", "H1", "M15", "M5"],
                "trend_votes": {"bullish": 9, "bearish": 1},
                "alignment": {
                    "state": "ALIGNED",
                    "timeframe_trends": {"H4": "bullish", "H1": "bullish", "M15": "bullish", "M5": "bullish"},
                    "higher_timeframe_conflict": False,
                    "lower_timeframe_conflict": False,
                    "cross_group_conflict": False,
                },
            }},
        }
        macro = {"data": {"gold_bias": "BULLISH", "news_risk": "LOW"}}
        view = build_trader_view(alert, decision, macro)
        self.assertEqual(view["decision"], "BUY")
        self.assertEqual(view["permission"], "ALLOW_BUYS")
        self.assertEqual(view["timeframe_conflict"], "LOW")
        self.assertEqual(view["timeframe_alignment"], "ALIGNED")
        self.assertEqual(view["timeframe_trends"]["H4"], "bullish")
        self.assertFalse(view["higher_timeframe_conflict"])
        self.assertFalse(view["cross_group_conflict"])
        self.assertFalse(view["execution_enabled"])

    def test_explicit_agent04_conflict_is_trader_visible(self):
        alert = {"data": {"permission": "CAUTION", "reason": "Conflict", "fresh": True, "execution_enabled": False}}
        decision = {
            "data": {"decision": "NO_TRADE", "confidence": 45, "risk": "HIGH", "reasons": []},
            "metadata": {"technical_fusion": {
                "trend_votes": {"bullish": 7, "bearish": 3},
                "alignment": {
                    "state": "CONFLICT",
                    "timeframe_trends": {"H4": "bullish", "H1": "bullish", "M15": "bearish", "M5": "bearish"},
                    "higher_timeframe_conflict": False,
                    "lower_timeframe_conflict": False,
                    "cross_group_conflict": True,
                },
            }},
        }
        view = build_trader_view(alert, decision, {})
        self.assertEqual(view["timeframe_alignment"], "CONFLICT")
        self.assertTrue(view["cross_group_conflict"])
        self.assertEqual(view["permission"], "CAUTION")
        self.assertFalse(view["execution_enabled"])

    def test_high_timeframe_disagreement_is_visible(self):
        alert = {"data": {"permission": "CAUTION", "reason": "Conflict", "fresh": True, "execution_enabled": False}}
        decision = {"data": {"decision": "NO_TRADE", "confidence": 45, "risk": "HIGH", "reasons": []}, "metadata": {"technical_fusion": {"trend_votes": {"bullish": 5, "bearish": 5}}}}
        view = build_trader_view(alert, decision, {})
        self.assertEqual(view["timeframe_conflict"], "HIGH")
        self.assertEqual(view["timeframe_alignment"], "NEUTRAL")
        self.assertEqual(view["permission"], "CAUTION")

    def test_unknown_alignment_metadata_fails_to_neutral_intelligence(self):
        alert = {"data": {"permission": "BLOCK_TRADING", "reason": "Safe block", "fresh": True, "execution_enabled": False}}
        decision = {"metadata": {"technical_fusion": {"alignment": {"state": "UNKNOWN"}}}}
        view = build_trader_view(alert, decision, {})
        self.assertEqual(view["timeframe_alignment"], "NEUTRAL")
        self.assertEqual(view["permission"], "BLOCK_TRADING")

    def test_view_strips_any_execution_authority(self):
        alert = {"data": {"permission": "ALLOW_BOTH", "reason": "Unexpected", "fresh": True, "execution_enabled": True}}
        view = build_trader_view(alert, {}, {})
        self.assertEqual(view["permission"], "BLOCK_TRADING")
        self.assertFalse(view["execution_enabled"])

    def test_missing_inputs_fail_safe(self):
        view = build_trader_view(None, None, None)
        self.assertEqual(view["decision"], "NO_TRADE")
        self.assertEqual(view["permission"], "BLOCK_TRADING")
        self.assertEqual(view["risk"], "EXTREME")
        self.assertEqual(view["timeframe_alignment"], "NEUTRAL")
        self.assertFalse(view["execution_enabled"])


if __name__ == "__main__":
    unittest.main()
