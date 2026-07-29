# ============================================================
# RAHUL AI TEAM
# MARKET STRUCTURE ANALYZER
# ============================================================

from market.indicators import ema


def _latest_swing(candles, field, mode, lookback=2):
    """Return the latest confirmed local swing, or a recent-window fallback."""
    if len(candles) < (lookback * 2) + 1:
        raise ValueError("Not enough candles for swing analysis.")

    for i in range(len(candles) - lookback - 1, lookback - 1, -1):
        value = candles[i][field]
        neighbours = [
            candles[j][field]
            for j in range(i - lookback, i + lookback + 1)
            if j != i
        ]
        if mode == "high" and value > max(neighbours):
            return value
        if mode == "low" and value < min(neighbours):
            return value

    recent = [c[field] for c in candles[-20:]]
    return max(recent) if mode == "high" else min(recent)


def analyze_structure(candles):
    """Analyze trend, support/resistance and confirmed local swings."""
    if len(candles) < 20:
        raise ValueError("Not enough candles for structure analysis.")

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    ema20 = ema(closes, 20)
    latest_close = closes[-1]

    if latest_close > ema20:
        trend = "Bullish"
    elif latest_close < ema20:
        trend = "Bearish"
    else:
        trend = "Sideways"

    return {
        "trend": trend,
        "support": min(lows[-20:]),
        "resistance": max(highs[-20:]),
        "swing_high": _latest_swing(candles, "high", "high"),
        "swing_low": _latest_swing(candles, "low", "low"),
    }
