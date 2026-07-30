import json
import tempfile
import unittest
from pathlib import Path

from history.observations import append_observation, append_outcome, build_observation, build_outcome


class HistoricalObservationTests(unittest.TestCase):
    def setUp(self):
        self.view = {
            "symbol": "XAUUSD", "decision": "BUY", "permission": "ALLOW_BUYS",
            "confidence": 82, "risk": "LOW", "macro_bias": "BULLISH",
            "news_risk": "LOW", "timeframe_conflict": "LOW",
            "trend_votes": {"bullish": 9, "bearish": 1}, "fresh": True,
            "execution_enabled": False,
        }

    def test_snapshot_is_deterministic_for_same_time_and_input(self):
        timestamp = "2026-07-30T12:00:00+00:00"
        first = build_observation(self.view, timestamp)
        second = build_observation(self.view, timestamp)
        self.assertEqual(first, second)
        self.assertFalse(first["prediction"]["execution_enabled"])
        self.assertEqual(first["outcomes"], {})

    def test_append_is_idempotent_and_does_not_rewrite_history(self):
        observation = build_observation(self.view, "2026-07-30T12:00:00+00:00")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "observations.jsonl"
            self.assertTrue(append_observation(path, observation))
            original = path.read_text(encoding="utf-8")
            self.assertFalse(append_observation(path, observation))
            self.assertEqual(path.read_text(encoding="utf-8"), original)
            self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 1)

    def test_outcome_is_separate_event_at_supported_horizon(self):
        observation = build_observation(self.view, "2026-07-30T12:00:00+00:00")
        before = json.dumps(observation, sort_keys=True)
        outcome = build_outcome(observation["observation_id"], "1h", 4100.25, "2026-07-30T13:00:00+00:00")
        self.assertEqual(outcome["horizon"], "1h")
        self.assertEqual(outcome["reference_price"], 4100.25)
        self.assertEqual(json.dumps(observation, sort_keys=True), before)

    def test_invalid_horizon_price_and_timestamp_fail_closed(self):
        with self.assertRaises(ValueError):
            build_outcome("abc", "30m", 4100)
        with self.assertRaises(ValueError):
            build_outcome("abc", "15m", 0)
        with self.assertRaises(ValueError):
            build_outcome("abc", "15m", float("nan"))
        with self.assertRaises(ValueError):
            build_outcome("abc", "15m", 4100, "not-a-time")
        with self.assertRaises(ValueError):
            build_observation(self.view, "2026-07-30T12:00:00")

    def test_snapshot_never_propagates_execution_authority(self):
        unsafe = dict(self.view)
        unsafe["execution_enabled"] = True
        observation = build_observation(unsafe, "2026-07-30T12:00:00+00:00")
        self.assertFalse(observation["prediction"]["execution_enabled"])

    def test_outcome_append_is_idempotent_per_observation_and_horizon(self):
        observation = build_observation(self.view, "2026-07-30T12:00:00+00:00")
        outcome = build_outcome(observation["observation_id"], "15m", 4101.0, "2026-07-30T12:15:00+00:00")
        with tempfile.TemporaryDirectory() as directory:
            observations = Path(directory) / "observations.jsonl"
            outcomes = Path(directory) / "outcomes.jsonl"
            append_observation(observations, observation)
            self.assertTrue(append_outcome(outcomes, outcome, observations))
            original = outcomes.read_text(encoding="utf-8")
            self.assertFalse(append_outcome(outcomes, outcome, observations))
            self.assertEqual(outcomes.read_text(encoding="utf-8"), original)

    def test_outcome_writer_rejects_orphan_and_corrupt_history(self):
        outcome = build_outcome("missing", "1h", 4100, "2026-07-30T13:00:00+00:00")
        with tempfile.TemporaryDirectory() as directory:
            observations = Path(directory) / "observations.jsonl"
            outcomes = Path(directory) / "outcomes.jsonl"
            observations.write_text('{"observation_id":"known"}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                append_outcome(outcomes, outcome, observations)
            outcomes.write_text("{corrupt\n", encoding="utf-8")
            known = build_outcome("known", "1h", 4100, "2026-07-30T13:00:00+00:00")
            with self.assertRaises(ValueError):
                append_outcome(outcomes, known, observations)


if __name__ == "__main__":
    unittest.main()
