# Deterministic macro/news scoring for XAUUSD.

BULLISH_TERMS = {
    "rate cut": 3, "dovish": 3, "lower yields": 2, "yields fall": 2,
    "dollar falls": 2, "weaker dollar": 2, "risk-off": 2, "geopolitical tension": 2,
    "inflation cools": 2, "recession": 1, "safe haven": 2,
}
BEARISH_TERMS = {
    "rate hike": 3, "hawkish": 3, "higher yields": 2, "yields rise": 2,
    "dollar rises": 2, "stronger dollar": 2, "risk-on": 1, "inflation accelerates": 2,
    "strong jobs": 2, "hot cpi": 3,
}
HIGH_IMPACT_TERMS = ("fomc", "fed", "cpi", "pce", "nfp", "payrolls", "powell", "rate decision")


def score_headline(title):
    text = title.lower().strip()
    score = sum(weight for term, weight in BULLISH_TERMS.items() if term in text)
    score -= sum(weight for term, weight in BEARISH_TERMS.items() if term in text)
    impact = "HIGH" if any(term in text for term in HIGH_IMPACT_TERMS) else "NORMAL"
    return score, impact


def aggregate_headlines(headlines):
    scored = []
    total = 0
    for item in headlines:
        title = item.get("title", "")
        score, impact = score_headline(title)
        total += score
        scored.append({**item, "gold_score": score, "impact": impact})

    if total >= 3:
        bias = "BULLISH"
    elif total <= -3:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    confidence = min(90, 50 + abs(total) * 5) if headlines else 0
    return {"bias": bias, "score": total, "confidence": confidence, "headlines": scored}
