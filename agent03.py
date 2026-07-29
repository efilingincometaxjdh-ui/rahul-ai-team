# RAHUL AI TEAM — AGENT 03: XAUUSD MACRO/NEWS INTELLIGENCE

from macro.rss import collect_headlines
from macro.scoring import aggregate_headlines
from utils.json_writer import write_state


def build_macro_state(headlines, collection_errors=None):
    result = aggregate_headlines(headlines)
    errors = list(collection_errors or [])
    if not headlines:
        status = "FAILED"
        errors.append("No macro/news headlines available")
    elif errors:
        status = "DEGRADED"
    else:
        status = "SUCCESS"

    data = {
        "gold_bias": result["bias"],
        "macro_score": result["score"],
        "confidence": result["confidence"],
        "headline_count": len(headlines),
        "high_impact_count": sum(1 for h in result["headlines"] if h["impact"] == "HIGH"),
        "headlines": result["headlines"],
    }
    return data, status, errors


def main():
    print("AGENT 03 — XAUUSD MACRO/NEWS INTELLIGENCE")
    headlines, collection_errors = collect_headlines()
    data, status, errors = build_macro_state(headlines, collection_errors)
    write_state(
        agent="Agent03", version="0.1", filename="agent03.json", data=data,
        status=status, errors=errors,
        metadata={"method": "official RSS + deterministic gold-impact scoring"},
    )
    print(f"Agent03 health: {status} | Gold bias: {data['gold_bias']} | Confidence: {data['confidence']}%")
    if status == "FAILED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
