# ============================================================
# RAHUL AI TEAM
# AGENT 02 — XAUUSD MARKET INTELLIGENCE
# ============================================================

import os
from datetime import datetime, timezone

from market.indicators import calculate_indicators
from market.structure import analyze_structure
from market.provider import CTraderOpenAPIProvider
from utils.json_writer import write_state

SYMBOL = "XAU/USD"
TIMEFRAMES = {"M5": "5min", "M15": "15min", "H1": "1h", "H4": "4h"}


def validate_ctrader_runtime():
    """Fail fast with safe diagnostics before opening a cTrader connection."""
    required = (
        "CTRADER_CLIENT_ID",
        "CTRADER_CLIENT_SECRET",
        "CTRADER_ACCESS_TOKEN",
    )
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            "cTrader runtime credentials missing: " + ", ".join(missing)
        )

    environment = os.environ.get("CTRADER_ENVIRONMENT", "demo").lower()
    if environment not in {"demo", "live"}:
        raise RuntimeError("CTRADER_ENVIRONMENT must be 'demo' or 'live'")

    print(
        "cTrader preflight: "
        f"environment={environment} "
        f"symbol={os.environ.get('CTRADER_SYMBOL', 'XAUUSD')} "
        f"client_id_present={bool(os.environ.get('CTRADER_CLIENT_ID'))} "
        f"client_secret_present={bool(os.environ.get('CTRADER_CLIENT_SECRET'))} "
        f"access_token_present={bool(os.environ.get('CTRADER_ACCESS_TOKEN'))}"
    )


def collect_market_data(provider=None):
    """Collect market data for all configured timeframes.

    cTrader is the only runtime market-data source. Providers used by tests
    may still implement the same fetch_candles interface; a cTrader provider
    uses one connection for all four timeframes to avoid unnecessary sessions.
    """
    if provider is None:
        validate_ctrader_runtime()
        provider = CTraderOpenAPIProvider()

    if hasattr(provider, "fetch_many"):
        return provider.fetch_many(TIMEFRAMES)

    market_data = {}
    for label, interval in TIMEFRAMES.items():
        print(f"Fetching XAUUSD {label}...")
        candles = provider.fetch_candles(label, interval)
        market_data[label] = candles
        if candles:
            latest = candles[-1]
            print(
                f"✅ {label}: {len(candles)} candles | Latest close: "
                f"{latest['close']:.2f} | Time: {latest['datetime']}"
            )
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
        "provider": "cTrader Open API",
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
            version="0.6",
            filename="agent02.json",
            data={},
            status="FAILED",
            errors=[str(error)],
            metadata={"symbol": SYMBOL, "provider": "cTrader Open API"},
        )
        print(f"❌ {error}")
        raise SystemExit(1)

    market_state, status, errors, metadata = build_market_state(market_data)
    write_state(
        agent="Agent02",
        version="0.6",
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
