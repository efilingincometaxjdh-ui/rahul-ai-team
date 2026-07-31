import tempfile
import unittest
from pathlib import Path

from history.collect_observation import collect_observation


class ObservationCollectorTests(unittest.TestCase):
    def setUp(self):
        self.view = {
            "symbol": "XAUUSD", "decision": "NO_TRADE", "permission": "BLOCK_TRADING",
            "confidence": 0, "risk": "EXTREME", "macro_bias": "NEUTRAL",
            "news_risk": "HIGH", "timeframe_conflict": "HIGH",
            "timeframe_alignment": "CONFLICT",
            "timeframe_trends": {"H4": "BULLISH", "H1": "BEARISH"},
            "higher_timeframe_conflict": True, "lower_timeframe_conflict": False,
            "cross_group_conflict": False, "trend_votes": {"bullish": 4, "bearish": 3},
            "fresh": False, "execution_enabled": False, "mode": "READ_ONLY",
        }
        self.state = {"health": {"status": "DEGRADED"}, "data": self.view}

    def test_collects_safe_blocked_state_as_append_only_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observations.jsonl"
            observation, appended = collect_observation(
                self.state, path, "2026-07-31T06:00:00+00:00"
            )
            self.assertTrue(appended)
            self.assertEqual(observation["prediction"]["permission"], "BLOCK_TRADING")
            self.assertFalse(observation["prediction"]["execution_enabled"])
            self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 1)

    def test_repeated_same_snapshot_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observations.jsonl"
            _, first = collect_observation(self.state, path, "2026-07-31T06:00:00+00:00")
            _, second = collect_observation(self.state, path, "2026-07-31T06:00:00+00:00")
            self.assertTrue(first)
            self.assertFalse(second)
            self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 1)

    def test_failed_or_malformed_envelope_fails_closed(self):
        cases = [
            None,
            {},
            {"health": {"status": "FAILED"}, "data": self.view},
            {"health": {"status": "UNKNOWN"}, "data": self.view},
            {"health": {"status": "SUCCESS"}, "data": None},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observations.jsonl"
            for state in cases:
                with self.subTest(state=state):
                    with self.assertRaises(ValueError):
                        collect_observation(state, path, "2026-07-31T06:00:00+00:00")
            self.assertFalse(path.exists())

    def test_execution_bearing_view_is_rejected_by_existing_contract(self):
        unsafe = dict(self.view)
        unsafe["execution_enabled"] = True
        state = {"health": {"status": "SUCCESS"}, "data": unsafe}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observations.jsonl"
            with self.assertRaises(ValueError):
                collect_observation(state, path, "2026-07-31T06:00:00+00:00")
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
