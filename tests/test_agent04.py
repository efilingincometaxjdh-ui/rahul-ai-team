import unittest
from decision.engine import build_decision


def technical(trend="Bullish", adx=30, status="SUCCESS"):
    frame = {"trend": trend, "adx": adx}
    return {"status": status, "data": {"M5": frame, "M15": frame, "H1": frame, "H4": frame}}


def macro(score=4, confidence=75, bias="BULLISH", status="SUCCESS"):
    return {"status": status, "data": {"macro_score": score, "confidence": confidence, "gold_bias": bias}}


class DecisionEngineTests(unittest.TestCase):
    def test_aligned_bullish_inputs(self):
        result = build_decision(technical(), macro())
        self.assertEqual(result["bias"], "BULLISH")
        self.assertTrue(result["agreement"])
        self.assertGreaterEqual(result["confidence"], 75)
        self.assertEqual(result["mode"], "ANALYSIS_ONLY")

    def test_aligned_bearish_inputs(self):
        result = build_decision(technical("Bearish"), macro(-4, 75, "BEARISH"))
        self.assertEqual(result["bias"], "BEARISH")
        self.assertTrue(result["agreement"])

    def test_conflict_reduces_confidence(self):
        aligned = build_decision(technical(), macro())
        conflict = build_decision(technical(), macro(-4, 75, "BEARISH"))
        self.assertLess(conflict["confidence"], aligned["confidence"])

    def test_degraded_source_caps_confidence(self):
        result = build_decision(technical(status="DEGRADED"), macro())
        self.assertLessEqual(result["confidence"], 60)
        self.assertNotEqual(result["setup_quality"], "STRONG")


if __name__ == "__main__":
    unittest.main()
