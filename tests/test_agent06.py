import unittest
from datetime import datetime, timedelta, timezone

from agent06 import build_alert

NOW = datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc)


def permission_state(permission="ALLOW_BUYS", status="SUCCESS", age_minutes=0, reason="test"):
    return {
        "agent": "Agent05",
        "version": "0.2",
        "generated_at": (NOW - timedelta(minutes=age_minutes)).isoformat(),
        "status": status,
        "data": {"permission": permission, "reason": reason},
    }


class Agent06Tests(unittest.TestCase):
    def test_fresh_valid_permission_is_reported_read_only(self):
        alert, status, errors, freshness = build_alert(permission_state(), now=NOW)
        self.assertEqual(status, "SUCCESS")
        self.assertEqual(alert["permission"], "ALLOW_BUYS")
        self.assertFalse(alert["execution_enabled"])
        self.assertTrue(alert["fresh"])
        self.assertTrue(freshness["fresh"])
        self.assertFalse(errors)

    def test_missing_state_fails_closed(self):
        alert, status, errors, _ = build_alert(None, now=NOW)
        self.assertEqual(status, "FAILED")
        self.assertEqual(alert["permission"], "BLOCK_TRADING")
        self.assertFalse(alert["execution_enabled"])
        self.assertTrue(errors)

    def test_stale_permission_fails_closed(self):
        alert, status, errors, _ = build_alert(permission_state(age_minutes=16), now=NOW)
        self.assertEqual(status, "FAILED")
        self.assertEqual(alert["permission"], "BLOCK_TRADING")
        self.assertTrue(errors)

    def test_unknown_permission_fails_closed(self):
        alert, status, errors, _ = build_alert(permission_state(permission="EXECUTE_NOW"), now=NOW)
        self.assertEqual(status, "FAILED")
        self.assertEqual(alert["permission"], "BLOCK_TRADING")
        self.assertTrue(errors)

    def test_degraded_upstream_cannot_emit_authority(self):
        alert, status, _, _ = build_alert(permission_state(permission="ALLOW_BUYS", status="DEGRADED"), now=NOW)
        self.assertEqual(status, "DEGRADED")
        self.assertEqual(alert["permission"], "CAUTION")
        self.assertFalse(alert["execution_enabled"])

    def test_block_trading_remains_non_executing(self):
        alert, status, _, _ = build_alert(permission_state(permission="BLOCK_TRADING"), now=NOW)
        self.assertEqual(status, "DEGRADED")
        self.assertEqual(alert["permission"], "BLOCK_TRADING")
        self.assertFalse(alert["execution_enabled"])


if __name__ == "__main__":
    unittest.main()
