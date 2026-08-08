import unittest

from history.scheduler import (
    due_horizons,
    is_observation_due,
    next_observation_slot,
    observation_slot,
)


class ObservationSchedulerTests(unittest.TestCase):
    def test_observation_slot_normalizes_to_utc_quarter_hour(self):
        self.assertEqual(
            observation_slot("2026-08-08T11:41:45+05:30").isoformat(),
            "2026-08-08T06:00:00+00:00",
        )

    def test_observation_due_when_no_snapshot_exists(self):
        self.assertTrue(is_observation_due(None, "2026-08-08T06:00:00+00:00"))

    def test_observation_due_only_after_slot_changes(self):
        self.assertFalse(
            is_observation_due(
                "2026-08-08T06:00:05+00:00",
                "2026-08-08T06:14:59+00:00",
            )
        )
        self.assertTrue(
            is_observation_due(
                "2026-08-08T06:00:05+00:00",
                "2026-08-08T06:15:00+00:00",
            )
        )

    def test_due_horizons_are_minimum_horizon_gates_only(self):
        observed = "2026-08-08T06:00:00+00:00"
        self.assertEqual(due_horizons(observed, "2026-08-08T06:14:59+00:00"), ())
        self.assertEqual(due_horizons(observed, "2026-08-08T06:15:00+00:00"), ("15m",))
        self.assertEqual(
            due_horizons(observed, "2026-08-08T07:00:00+00:00"),
            ("15m", "1h"),
        )
        self.assertEqual(
            due_horizons(observed, "2026-08-08T10:00:00+00:00"),
            ("15m", "1h", "4h"),
        )

    def test_next_slot_is_deterministic(self):
        self.assertEqual(
            next_observation_slot("2026-08-08T06:00:01+00:00").isoformat(),
            "2026-08-08T06:15:00+00:00",
        )

    def test_naive_timestamps_fail_closed(self):
        with self.assertRaises(ValueError):
            observation_slot("2026-08-08T06:00:00")
        with self.assertRaises(ValueError):
            due_horizons("2026-08-08T06:00:00", "2026-08-08T06:15:00+00:00")


if __name__ == "__main__":
    unittest.main()
