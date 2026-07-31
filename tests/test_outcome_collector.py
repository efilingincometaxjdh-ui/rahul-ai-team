import json
import tempfile
import unittest
from pathlib import Path

from history.collect_outcome import collect_outcome
from history.observations import append_observation, build_observation


class OutcomeCollectorTests(unittest.TestCase):
    def setUp(self):
        self.view = {
            "symbol": "XAUUSD", "decision": "NO_TRADE", "permission": "BLOCK_TRADING",
            "confidence": 0, "risk": "EXTREME", "macro_bias": "NEUTRAL",
            "news_risk": "HIGH", "timeframe_conflict": "HIGH", "fresh": False,
            "execution_enabled": False, "mode": "READ_ONLY",
        }
        self.quote = {
            "provider": "gold-api.com", "symbol": "XAUUSD", "market": "SPOT",
            "quote_currency": "USD", "price": 4100.25,
            "observed_at": "2026-07-31T06:15:00+00:00", "requires_credentials": False,
        }

    def _history(self, directory):
        observations = Path(directory) / "observations.jsonl"
        outcomes = Path(directory) / "outcomes.jsonl"
        observation = build_observation(self.view, "2026-07-31T06:00:00+00:00")
        append_observation(observations, observation)
        return observation, observations, outcomes

    def test_appends_outcome_using_provider_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            observation, observations, outcomes = self._history(directory)
            outcome, appended = collect_outcome(
                observation["observation_id"], "15m", self.quote, observations, outcomes
            )
            self.assertTrue(appended)
            self.assertEqual(outcome["reference_price"], 4100.25)
            self.assertEqual(outcome["measured_at"], self.quote["observed_at"])
            record = json.loads(outcomes.read_text(encoding="utf-8").strip())
            self.assertEqual(record, outcome)

    def test_same_observation_horizon_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            observation, observations, outcomes = self._history(directory)
            args = (observation["observation_id"], "15m", self.quote, observations, outcomes)
            self.assertTrue(collect_outcome(*args)[1])
            self.assertFalse(collect_outcome(*args)[1])
            self.assertEqual(len(outcomes.read_text(encoding="utf-8").splitlines()), 1)

    def test_rejects_quote_before_horizon_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            observation, observations, outcomes = self._history(directory)
            early = dict(self.quote, observed_at="2026-07-31T06:14:59+00:00")
            with self.assertRaises(ValueError):
                collect_outcome(observation["observation_id"], "15m", early, observations, outcomes)
            self.assertFalse(outcomes.exists())

    def test_rejects_unsafe_reference_evidence_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            observation, observations, outcomes = self._history(directory)
            unsafe = dict(self.quote, market="FUTURES")
            with self.assertRaises(ValueError):
                collect_outcome(observation["observation_id"], "15m", unsafe, observations, outcomes)
            self.assertFalse(outcomes.exists())

    def test_rejects_unknown_observation_and_horizon(self):
        with tempfile.TemporaryDirectory() as directory:
            _, observations, outcomes = self._history(directory)
            with self.assertRaises(ValueError):
                collect_outcome("missing", "15m", self.quote, observations, outcomes)
            with self.assertRaises(ValueError):
                collect_outcome("missing", "1d", self.quote, observations, outcomes)
            self.assertFalse(outcomes.exists())


if __name__ == "__main__":
    unittest.main()
