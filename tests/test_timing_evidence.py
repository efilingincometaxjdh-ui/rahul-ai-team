import json
import tempfile
import unittest
from pathlib import Path

from history.timing_evidence import build_timing_record, write_timing_record


class TimingEvidenceTests(unittest.TestCase):
    def test_normalizes_to_utc_quarter_hour_slot(self):
        record = build_timing_record(
            run_id="42",
            workflow_started_at="2026-08-12T18:47:10+05:30",
            workflow_finished_at="2026-08-12T18:48:10+05:30",
            latest_reference_at="2026-08-12T18:45:00+05:30",
        )
        self.assertEqual(record["observation_slot"], "2026-08-12T13:15:00Z")
        self.assertEqual(record["scheduler_delay_seconds"], 130.0)

    def test_reference_age_is_deterministic(self):
        record = build_timing_record(
            run_id="43",
            workflow_started_at="2026-08-12T13:30:00Z",
            workflow_finished_at="2026-08-12T13:31:30Z",
            latest_reference_at="2026-08-12T13:25:00Z",
        )
        self.assertEqual(record["reference_age_seconds"], 390.0)

    def test_naive_timestamp_fails_closed(self):
        with self.assertRaises(ValueError):
            build_timing_record(
                run_id="44",
                workflow_started_at="2026-08-12T13:30:00",
                workflow_finished_at="2026-08-12T13:31:00Z",
                latest_reference_at="2026-08-12T13:25:00Z",
            )

    def test_future_reference_fails_closed(self):
        with self.assertRaises(ValueError):
            build_timing_record(
                run_id="45",
                workflow_started_at="2026-08-12T13:30:00Z",
                workflow_finished_at="2026-08-12T13:31:00Z",
                latest_reference_at="2026-08-12T13:32:00Z",
            )

    def test_append_is_jsonl_and_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "timing.jsonl"
            first = write_timing_record(
                path,
                run_id="46",
                workflow_started_at="2026-08-12T13:30:01Z",
                workflow_finished_at="2026-08-12T13:31:01Z",
                latest_reference_at="2026-08-12T13:30:00Z",
            )
            second = write_timing_record(
                path,
                run_id="47",
                workflow_started_at="2026-08-12T13:45:01Z",
                workflow_finished_at="2026-08-12T13:46:01Z",
                latest_reference_at="2026-08-12T13:45:00Z",
            )
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows, [first, second])


if __name__ == "__main__":
    unittest.main()
