import unittest

from history.reference_price import validate_reference_quote


class ReferencePriceContractTests(unittest.TestCase):
    def setUp(self):
        self.quote = {
            "provider": "validated-zero-cost-source",
            "symbol": "XAUUSD",
            "market": "SPOT",
            "quote_currency": "USD",
            "price": 4100.25,
            "observed_at": "2026-07-31T07:30:00+00:00",
            "requires_credentials": False,
        }

    def test_accepts_explicit_spot_xauusd_evidence(self):
        result = validate_reference_quote(self.quote)
        self.assertEqual(result["symbol"], "XAUUSD")
        self.assertEqual(result["market"], "SPOT")
        self.assertEqual(result["price"], 4100.25)
        self.assertFalse(result["requires_credentials"])

    def test_rejects_futures_or_proxy_instruments(self):
        cases = [
            {"symbol": "GC=F", "market": "FUTURES"},
            {"symbol": "GLD", "market": "ETF"},
            {"symbol": "XAUUSD", "market": "FUTURES"},
        ]
        for changes in cases:
            quote = dict(self.quote)
            quote.update(changes)
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    validate_reference_quote(quote)

    def test_rejects_credentials_unknown_provider_and_bad_currency(self):
        cases = [
            ("requires_credentials", True),
            ("requires_credentials", None),
            ("provider", ""),
            ("quote_currency", "EUR"),
        ]
        for key, value in cases:
            quote = dict(self.quote)
            quote[key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaises(ValueError):
                    validate_reference_quote(quote)

    def test_rejects_invalid_price_and_timestamp(self):
        cases = [
            ("price", 0),
            ("price", float("nan")),
            ("price", True),
            ("observed_at", "not-a-time"),
            ("observed_at", "2026-07-31T07:30:00"),
        ]
        for key, value in cases:
            quote = dict(self.quote)
            quote[key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaises(ValueError):
                    validate_reference_quote(quote)


if __name__ == "__main__":
    unittest.main()
