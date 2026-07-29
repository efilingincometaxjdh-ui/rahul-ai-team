import unittest

from agent03 import build_macro_state, classify_news_risk
from macro.scoring import score_headline, aggregate_headlines


class MacroScoringTests(unittest.TestCase):
    def test_dovish_rate_cut_is_bullish_gold(self):
        score, impact = score_headline("Fed signals dovish rate cut after FOMC")
        self.assertGreater(score, 0)
        self.assertEqual(impact, "HIGH")

    def test_hawkish_hike_is_bearish_gold(self):
        score, impact = score_headline("Fed turns hawkish and signals rate hike")
        self.assertLess(score, 0)
        self.assertEqual(impact, "HIGH")

    def test_aggregate_bias(self):
        result = aggregate_headlines([
            {"title": "Fed signals dovish rate cut"},
            {"title": "Dollar falls as yields fall"},
        ])
        self.assertEqual(result["bias"], "BULLISH")
        self.assertGreater(result["confidence"], 50)


class NewsRiskTests(unittest.TestCase):
    def test_no_high_impact_is_low(self):
        self.assertEqual(classify_news_risk([{"impact": "NORMAL"}]), "LOW")

    def test_one_high_impact_is_medium(self):
        self.assertEqual(classify_news_risk([{"impact": "HIGH"}]), "MEDIUM")

    def test_multiple_high_impact_is_high(self):
        self.assertEqual(classify_news_risk([{"impact": "HIGH"}] * 3), "HIGH")

    def test_rss_scoring_never_invents_extreme(self):
        self.assertNotEqual(classify_news_risk([{"impact": "HIGH"}] * 20), "EXTREME")


class Agent03HealthTests(unittest.TestCase):
    def test_no_headlines_fails(self):
        data, status, errors = build_macro_state([])
        self.assertEqual(status, "FAILED")
        self.assertEqual(data["headline_count"], 0)
        self.assertTrue(errors)

    def test_collection_error_with_data_is_degraded(self):
        data, status, errors = build_macro_state([{"title": "Fed policy update"}], ["one feed failed"])
        self.assertEqual(status, "DEGRADED")
        self.assertEqual(data["headline_count"], 1)
        self.assertEqual(data["news_risk"], "MEDIUM")
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
