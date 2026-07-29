# ============================================================
# RAHUL AI TEAM
# AGENT 02 — XAUUSD MARKET INTELLIGENCE
# ============================================================

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from market.indicators import calculate_indicators
from market.structure import analyze_structure
from utils.json_writer import write_state

API_KEY = os.getenv("TWELVE_DATA_API_KEY")
BASE_URL = "https://api.twelvedata.com/time_series"
SYMBOL = "XAU/USD"
TIMEFRAMES = {"M5": "5min", "M15": "15min", "H1": "1h", "H4": "4h"}
OUTPUT_SIZE = 100
REQUEST_TIMEOUT = 15


def fetch_candles(label, interval):
    if not API_KEY:
        raise RuntimeError("TWELVE_DATA_API_KEY environment variable is missing.")

    params = {
        "symbol": SYMBOL,
        "interval": interval,
        "outputsize": OUTPUT_SIZE,
        "apikey": API_KEY,
        "format": "JSON",
    }
    request = urllib.request.Request(
        BASE_URL + "?" + urllib.parse.urlencode(params),
        headers={"User-Agent": "Rahul-AI-Team-Agent02/1.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        print(f"❌ {label}: Request failed: {error}")
        return None

    if data.get("status") == "error":
        print(f"❌ {label}: Twelve Data error: {data.get('message', 'Unknown error')}")
        return None

    values = data.get("values")
    if not values:
        print(f"❌ {label}: No candle data received.")
        return None

    candles = []
    for item in values:
        try:
            candles.append({
                "datetime": item["datetime"],
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
            })
        except (KeyError, TypeError, ValueError):
            continue

    if not candles:
        print(f"❌ {label}: No valid candles after validation.")
        return None

    candles.reverse()
    return candles


def collect_market_data():
    market_data = {}
    for label, interval in TIMEFRAMES.items():
        print(f"Fetching XAUUSD {label}...")
        candles = fetch_candles(label, interval)
        market_data[label] = candles
        if candles:
            latest = candles[-1]
            print(f"✅ {label}: {len(candles)} candles | Latest close: {latest['close']:.2f} | Time: {latest['datetime']}")
    return market_data


def validate_market_data(market_data):
    available = [timeframe for timeframe, candles in market_data.items() if candles]
    missing = [timeframe for timeframe, candles in market_data.items() if not candles]
    return available, missing


def build_market_state(market_data):
    available, missing = validate_market_data(market_data)
    market_state = {}
    errors = []

    for timeframe in available:
        try:
            indicators = calculate_indicators(market_data[timeframe])
            structure = analyze_structure(market_data[timeframe])
            market_state[timeframe] = {
                "ema20": indicators["ema20"],
                "ema50": indicators["ema50"],
                "rsi": indicators["rsi14"],
                "adx": indicators["adx14"],
                "atr": indicators["atr14"],
                "trend": structure["trend"],
                "support": structure["support"],
                "resistance": structure["resistance"],
                "swing_high": structure["swing_high"],
                "swing_low": structure["swing_low"],
            }
        except Exception as error:
            errors.append(f"{timeframe}: analysis failed: {error}")

    for timeframe in missing:
        errors.append(f"{timeframe}: market data unavailable")

    if not market_state:
        status = "FAILED"
    elif errors:
        status = "DEGRADED"
    else:
        status = "SUCCESS"

    metadata = {
        "symbol": SYMBOL,
        "requested_timeframes": list(TIMEFRAMES.keys()),
        "available_timeframes": available,
        "missing_timeframes": missing,
    }
    return market_state, status, errors, metadata


def main():
    print("\n🤖 RAHUL AI TEAM")
    print("=" * 60)
    print("AGENT 02 — XAUUSD MARKET INTELLIGENCE")
    print("=" * 60)

    try:
        market_data = collect_market_data()
    except RuntimeError as error:
        write_state(
            agent="Agent02",
            version="0.4",
            filename="agent02.json",
            data={},
            status="FAILED",
            errors=[str(error)],
            metadata={"symbol": SYMBOL},
        )
        print(f"❌ {error}")
        raise SystemExit(1)

    market_state, status, errors, metadata = build_market_state(market_data)
    write_state(
        agent="Agent02",
        version="0.4",
        filename="agent02.json",
        data=market_state,
        status=status,
        errors=errors,
        metadata=metadata,
    )

    print(f"UTC: {datetime.now(timezone.utc).isoformat()}")
    print(f"Agent02 health: {status}")
    print(f"Usable timeframes: {', '.join(market_state) if market_state else 'NONE'}")
    if errors:
        for error in errors:
            print(f"⚠️ {error}")

    if status == "FAILED":
        raise SystemExit(1)

    print("✅ Agent02 state written to data/current/agent02.json")


if __name__ == "__main__":
    main()
