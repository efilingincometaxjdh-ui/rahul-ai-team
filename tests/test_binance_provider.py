import json
import unittest

from market.binance import BinancePublicProvider


class TestBinancePublicProvider(unittest.TestCase):
    def test_fetch_price_is_read_only_and_normalized(self):
        def fake_get(url):
            self.assertIn("/api/v3/ticker/price", url)
            return json.dumps({"symbol": "BTCUSDT", "price": "123.45"}).encode()

        provider = BinancePublicProvider(http_get=fake_get)
        result = provider.fetch_price()

        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertEqual(result["price"], 123.45)
        self.assertEqual(result["source"], "binance_spot")

    def test_fetch_candles_maps_public_klines(self):
        rows = [
            [1700000000000, "100", "110", "90", "105", "42"],
            [1700000060000, "105", "112", "101", "109", "37"],
        ]

        def fake_get(url):
            self.assertIn("interval=1m", url)
            return json.dumps(rows).encode()

        provider = BinancePublicProvider(symbol="BTCUSDT", http_get=fake_get)
        candles = provider.fetch_candles("1min", "1min", limit=2)

        self.assertEqual(len(candles), 2)
        self.assertEqual(candles[0]["open"], 100.0)
        self.assertEqual(candles[0]["high"], 110.0)
        self.assertEqual(candles[0]["low"], 90.0)
        self.assertEqual(candles[0]["close"], 105.0)
        self.assertEqual(candles[0]["volume"], 42.0)
        self.assertEqual(candles[0]["symbol"], "BTCUSDT")
        self.assertEqual(candles[0]["source"], "binance_spot")

    def test_rejects_invalid_limit(self):
        provider = BinancePublicProvider(http_get=lambda _: b"[]")
        with self.assertRaises(ValueError):
            provider.fetch_candles("1min", "1min", limit=0)

    def test_rejects_malformed_kline(self):
        provider = BinancePublicProvider(http_get=lambda _: json.dumps([[1, 2]]).encode())
        with self.assertRaises(RuntimeError):
            provider.fetch_candles("1min", "1min")

    def test_rejects_unknown_interval(self):
        provider = BinancePublicProvider(http_get=lambda _: b"[]")
        with self.assertRaises(ValueError):
            provider.fetch_candles("10min", "10min")


if __name__ == "__main__":
    unittest.main()
