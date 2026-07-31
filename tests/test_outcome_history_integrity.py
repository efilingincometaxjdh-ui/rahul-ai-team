import json
import tempfile
import unittest
from pathlib import Path

from history.observations import append_observation, append_outcome, build_observation, build_outcome


class ExistingOutcomeHistoryIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.view = {
            "symbol": "XAUUSD", "decision": "NO_TRADE", "permission": "BLOCK_TRADING",
            "confidence": 0, "risk": "EXTREME", "macro_bias": "NEUTRAL",
            "news_risk": "HIGH", "timeframe_conflict": "HIGH", "fresh": False,
            "execution_enabled": False, "mode": "READ_ONLY",
        }

    def _paths(self, directory):
        observations = Path(directory) / "observations.jsonl"
        outcomes = Path(directory) / "outcomes.jsonl"
        observation = build_observation(self.view, "2026-07-31T12:00:00+00:00")
        append_observation(observations, observation)
        candidate = build_outcome(observation["observation_id"], "1h", 4100, "2026-07-31T13:00:00+00:00")
        return observation, candidate, observations, outcomes

    def test_existing_record_must_be_semantically_valid_before_idempotency(self):
        corruptions = [
            {"horizon": "1d"},
            {"reference_price": 0},
            {"reference_price": float("nan")},
            {"measured_at": "not-a-time"},
            {"measured_at": "2026-07-31T12:59:59+00:00"},
            {"schema_version": 99},
        ]
        for changes in corruptions:
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as directory:
                _, candidate, observations, outcomes = self._paths(directory)
                existing = dict(candidate)
                existing.update(changes)
                outcomes.write_text(json.dumps(existing) + "\n", encoding="utf-8")
                before = outcomes.read_text(encoding="utf-8")
                with self.assertRaises(ValueError):
                    append_outcome(outcomes, candidate, observations)
                self.assertEqual(outcomes.read_text(encoding="utf-8"), before)

    def test_existing_outcome_must_reference_real_source_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            _, candidate, observations, outcomes = self._paths(directory)
            orphan = dict(candidate, observation_id="orphan")
            outcomes.write_text(json.dumps(orphan) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                append_outcome(outcomes, candidate, observations)

    def test_duplicate_existing_outcome_keys_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            _, candidate, observations, outcomes = self._paths(directory)
            line = json.dumps(candidate) + "\n"
            outcomes.write_text(line + line, encoding="utf-8")
            with self.assertRaises(ValueError):
                append_outcome(outcomes, candidate, observations)


if __name__ == "__main__":
    unittest.main()
