# RAHUL AI TEAM — AGENT 04 DECISION ENGINE

TIMEFRAME_WEIGHTS = {"H4": 3, "H1": 2, "M15": 1, "M5": 0.5}


def technical_score(agent02):
    data = agent02.get("data", {})
    score, reasons = 0.0, []
    for timeframe, weight in TIMEFRAME_WEIGHTS.items():
        state = data.get(timeframe)
        if not state:
            continue
        trend = str(state.get("trend", "")).lower()
        direction = 1 if trend == "bullish" else -1 if trend == "bearish" else 0
        score += weight * direction
        if direction:
            reasons.append(f"{timeframe} {trend}")
        adx = state.get("adx")
        if direction and isinstance(adx, (int, float)) and adx >= 25:
            score += 0.5 * direction
            reasons.append(f"{timeframe} trend strength ADX {adx:.1f}")
    return score, reasons


def macro_score(agent03):
    data = agent03.get("data", {})
    raw = data.get("macro_score", 0)
    confidence = data.get("confidence", 0)
    raw = raw if isinstance(raw, (int, float)) else 0
    confidence = confidence if isinstance(confidence, (int, float)) else 0
    weighted = max(-6, min(6, raw)) * max(0, min(100, confidence)) / 100
    return weighted, [f"Macro bias {data.get('gold_bias', 'NEUTRAL')} ({confidence:.0f}% confidence)"]


def build_decision(agent02, agent03):
    tech, tech_reasons = technical_score(agent02)
    macro, macro_reasons = macro_score(agent03)
    total = tech + macro
    bias = "BULLISH" if total >= 3 else "BEARISH" if total <= -3 else "NEUTRAL"
    agreement = (tech > 0 and macro > 0) or (tech < 0 and macro < 0)
    conflict = (tech > 0 > macro) or (macro > 0 > tech)
    confidence = max(0, min(90, int(50 + abs(total) * 5 + (8 if agreement else 0) - (10 if conflict else 0))))

    source_health = {"agent02": agent02.get("status", "UNKNOWN"), "agent03": agent03.get("status", "UNKNOWN")}
    degraded = any(value != "SUCCESS" for value in source_health.values())
    if degraded:
        confidence = min(confidence, 60)
    quality = "STRONG" if confidence >= 75 and not degraded else "MODERATE" if confidence >= 60 else "WEAK"

    return {
        "symbol": "XAUUSD", "bias": bias, "confidence": confidence,
        "setup_quality": quality, "technical_score": round(tech, 2),
        "macro_score": round(macro, 2), "combined_score": round(total, 2),
        "agreement": agreement, "source_health": source_health,
        "reasons": tech_reasons + macro_reasons, "mode": "ANALYSIS_ONLY",
    }
