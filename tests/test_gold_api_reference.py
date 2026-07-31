import unittest

from history.gold_api_reference import normalize_gold_api_xau


class GoldApiReferenceAdapterTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "name": "Gold",
            "price": 4100.25,
            "symbol": "XAU",
            "updatedAt": "2026-07-31T10:30:00Z",
            "updatedAtReadable": "a few seconds ago",
        }

    def test_normalizes_xau_payload_to_spot_xauusd_evidence(self):
        quote = normalize_gold_api_xau(self.payload)
        self.assertEqual(quote["provider"], "gold-api.com")
        self.assertEqual(quote["symbol"], "XAUUSD")
        self.assertEqual(quote["market"], "SPOT")
        self.assertEqual(quote["quote_currency"], "USD")
        self.assertEqual(quote["price"], 4100.25)
        self.assertEqual(quote["observed_at"], "2026-07-31T10:30:00Z")
        self.assertFalse(quote["requires_credentials"])

    def test_rejects_wrong_asset(self):
        payload = dict(self.payload, symbol="XAG")
        with self.assertRaises(ValueError):
            normalize_gold_api_xau(payload)

    def test_rejects_missing_provider_timestamp(self):
        payload = dict(self.payload)
        payload.pop("updatedAt")
        with self.assertRaises(ValueError):
            normalize_gold_api_xau(payload)

    def test_rejects_invalid_price_via_reference_contract(self):
        for price in (None, 0, -1, True, float("nan")):
            with self.subTest(price=price):
                with self.assertRaises(ValueError):
                    normalize_gold_api_xau(dict(self.payload, price=price))

    def test_rejects_malformed_or_timezone_naive_timestamp(self):
        for timestamp in ("not-a-time", "2026-07-31T10:30:00"):
            with self.subTest(timestamp=timestamp):
                with self.assertRaises(ValueError):
                    normalize_gold_api_xau(dict(self.payload, updatedAt=timestamp))

    def test_rejects_non_dictionary_payload(self):
        with self.assertRaises(ValueError):
            normalize_gold_api_xau([])


if __name__ == "__main__":
    unittest.main()
