import json
import tempfile
import unittest
from pathlib import Path

from history.analytics import build_evidence_coverage
from history.observations import append_observation, append_outcome, build_observation, build_outcome


class EvidenceCoverageTests(unittest.TestCase):
    def _view(self):
        return {
            "symbol": "XAUUSD",
            "mode": "READ_ONLY",
            "execution_enabled": False,
            "decision": "NO_TRADE",
            "permission": "BLOCK_TRADING",
            "confidence": 0,
            "risk": "EXTREME",
            "timeframe_conflict": "HIGH",
            "timeframe_alignment": "CONFLICT",
            "timeframe_trends": {"H4": "BULLISH", "H1": "BEARISH", "M15": "NEUTRAL", "M5": "NEUTRAL"},
            "higher_timeframe_conflict": True,
            "lower_timeframe_conflict": False,
            "cross_group_conflict": True,
            "fresh": True,
        }

    def test_reports_horizon_and_complete_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            observations = Path(temp) / "observations.jsonl"
            outcomes = Path(temp) / "outcomes.jsonl"
            observation = build_observation(self._view(), "2026-08-01T00:00:00+00:00")
            append_observation(observations, observation)
            for horizon, measured_at in (("15m", "2026-08-01T00:15:00+00:00"), ("1h", "2026-08-01T01:00:00+00:00"), ("4h", "2026-08-01T04:00:00+00:00")):
                append_outcome(outcomes, build_outcome(observation["observation_id"], horizon, 3300, measured_at), observations)

            report = build_evidence_coverage(observations, outcomes)

            self.assertEqual("SUCCESS", report["health"])
            self.assertEqual(1, report["observations"])
            self.assertEqual(3, report["outcomes"])
            self.assertEqual({"15m": 1, "1h": 1, "4h": 1}, report["coverage_by_horizon"])
            self.assertEqual({"15m": 0, "1h": 0, "4h": 0}, report["missing_by_horizon"])
            self.assertEqual({"15m": "COMPLETE", "1h": "COMPLETE", "4h": "COMPLETE"}, report["coverage_status_by_horizon"])
            self.assertEqual(1, report["complete_observations"])
            self.assertEqual(0, report["incomplete_observations"])
            self.assertFalse(report["execution_enabled"])
            self.assertEqual("READ_ONLY", report["mode"])

    def test_partial_coverage_is_trader_readable(self):
        with tempfile.TemporaryDirectory() as temp:
            observations = Path(temp) / "observations.jsonl"
            outcomes = Path(temp) / "outcomes.jsonl"
            first = build_observation(self._view(), "2026-08-01T00:00:00+00:00")
            second = build_observation(self._view(), "2026-08-01T00:01:00+00:00")
            append_observation(observations, first)
            append_observation(observations, second)
            append_outcome(outcomes, build_outcome(first["observation_id"], "15m", 3300, "2026-08-01T00:15:00+00:00"), observations)

            report = build_evidence_coverage(observations, outcomes)

            self.assertEqual({"15m": 1, "1h": 2, "4h": 2}, report["missing_by_horizon"])
            self.assertEqual({"15m": "PARTIAL", "1h": "EMPTY", "4h": "EMPTY"}, report["coverage_status_by_horizon"])
            self.assertFalse(report["execution_enabled"])

    def test_incomplete_observation_is_visible(self):
        with tempfile.TemporaryDirectory() as temp:
            observations = Path(temp) / "observations.jsonl"
            outcomes = Path(temp) / "outcomes.jsonl"
            observation = build_observation(self._view(), "2026-08-01T00:00:00+00:00")
            append_observation(observations, observation)
            append_outcome(outcomes, build_outcome(observation["observation_id"], "15m", 3300, "2026-08-01T00:15:00+00:00"), observations)

            report = build_evidence_coverage(observations, outcomes)

            self.assertEqual("SUCCESS", report["health"])
            self.assertEqual(1, report["incomplete_observations"])
            self.assertEqual(0, report["complete_observations"])

    def test_empty_history_has_empty_status_without_authority(self):
        with tempfile.TemporaryDirectory() as temp:
            report = build_evidence_coverage(Path(temp) / "observations.jsonl", Path(temp) / "outcomes.jsonl")

            self.assertEqual("SUCCESS", report["health"])
            self.assertEqual({"15m": "EMPTY", "1h": "EMPTY", "4h": "EMPTY"}, report["coverage_status_by_horizon"])
            self.assertEqual({"15m": 0, "1h": 0, "4h": 0}, report["missing_by_horizon"])
            self.assertFalse(report["execution_enabled"])

    def test_corrupt_observation_fails_closed_without_partial_metrics(self):
        with tempfile.TemporaryDirectory() as temp:
            observations = Path(temp) / "observations.jsonl"
            outcomes = Path(temp) / "outcomes.jsonl"
            observation = build_observation(self._view(), "2026-08-01T00:00:00+00:00")
            observation["prediction"]["execution_enabled"] = True
            observations.write_text(json.dumps(observation) + "\n", encoding="utf-8")

            report = build_evidence_coverage(observations, outcomes)

            self.assertEqual("FAILED", report["health"])
            self.assertEqual(0, report["observations"])
            self.assertEqual(0, report["outcomes"])
            self.assertEqual({"15m": "EMPTY", "1h": "EMPTY", "4h": "EMPTY"}, report["coverage_status_by_horizon"])
            self.assertFalse(report["execution_enabled"])

    def test_corrupt_outcome_fails_closed_without_partial_metrics(self):
        with tempfile.TemporaryDirectory() as temp:
            observations = Path(temp) / "observations.jsonl"
            outcomes = Path(temp) / "outcomes.jsonl"
            observation = build_observation(self._view(), "2026-08-01T00:00:00+00:00")
            append_observation(observations, observation)
            outcomes.write_text(json.dumps({
                "observation_id": observation["observation_id"],
                "horizon": "15m",
                "reference_price": -1,
                "measured_at": "2026-08-01T00:15:00+00:00",
                "schema_version": 1,
            }) + "\n", encoding="utf-8")

            report = build_evidence_coverage(observations, outcomes)

            self.assertEqual("FAILED", report["health"])
            self.assertEqual({"15m": 0, "1h": 0, "4h": 0}, report["coverage_by_horizon"])
            self.assertEqual({"15m": 0, "1h": 0, "4h": 0}, report["missing_by_horizon"])

    def test_duplicate_observation_ids_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            observations = Path(temp) / "observations.jsonl"
            outcomes = Path(temp) / "outcomes.jsonl"
            observation = build_observation(self._view(), "2026-08-01T00:00:00+00:00")
            line = json.dumps(observation) + "\n"
            observations.write_text(line + line, encoding="utf-8")

            report = build_evidence_coverage(observations, outcomes)

            self.assertEqual("FAILED", report["health"])
            self.assertEqual(0, report["complete_observations"])


if __name__ == "__main__":
    unittest.main()
