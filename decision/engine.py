# ============================================================
# RAHUL AI TEAM
# AGENT 04 — DECISION ENGINE
# Recovered from repository Decision Engine v1.0
# ============================================================


class DecisionEngine:
    VALID_BIASES = {"BULLISH", "BEARISH", "NEUTRAL"}
    VALID_RISKS = {"LOW", "MEDIUM", "HIGH", "EXTREME"}

    def evaluate(self, macro, technical):
        """Fuse normalized macro and technical evidence deterministically."""
        if not isinstance(macro, dict) or not isinstance(technical, dict):
            raise ValueError("macro and technical inputs must be dictionaries")

        risk = str(macro.get("news_risk", "HIGH")).upper()
        gold_bias = str(macro.get("gold_bias", "NEUTRAL")).upper()
        if risk not in self.VALID_RISKS:
            risk = "HIGH"
        if gold_bias not in self.VALID_BIASES:
            gold_bias = "NEUTRAL"

        if risk == "EXTREME":
            return {
                "decision": "NO_TRADE",
                "confidence": 100,
                "risk": "EXTREME",
                "reasons": ["Extreme macro news risk."],
            }

        reasons = []
        score = 50

        if gold_bias == "BULLISH":
            score += 15
            reasons.append("Macro supports Gold")
        elif gold_bias == "BEARISH":
            score -= 15
            reasons.append("Macro bearish for Gold")

        trend = str(technical.get("trend", "Neutral")).lower()
        if trend == "bullish":
            score += 15
            reasons.append("Trend is Bullish")
        elif trend == "bearish":
            score -= 15
            reasons.append("Trend is Bearish")

        ema20 = technical.get("ema20")
        ema50 = technical.get("ema50")
        if ema20 is not None and ema50 is not None:
            if ema20 > ema50:
                score += 10
                reasons.append("EMA20 above EMA50")
            elif ema20 < ema50:
                score -= 10
                reasons.append("EMA20 below EMA50")
            else:
                reasons.append("EMA20 equals EMA50")
        else:
            reasons.append("EMA evidence unavailable")

        adx = technical.get("adx")
        if adx is not None and adx >= 25:
            score += 5
            reasons.append("Strong trend confirmed")
        else:
            reasons.append("Weak or unavailable trend strength")

        rsi = technical.get("rsi")
        if rsi is not None:
            if rsi > 70:
                score -= 5
                reasons.append("RSI overbought")
            elif rsi < 30:
                score += 5
                reasons.append("RSI oversold")

        score = max(0, min(score, 100))

        if score >= 80:
            decision = "STRONG_BULLISH"
        elif score >= 65:
            decision = "BULLISH"
        elif score >= 45:
            decision = "NEUTRAL"
        elif score >= 25:
            decision = "BEARISH"
        else:
            decision = "STRONG_BEARISH"

        return {
            "decision": decision,
            "confidence": score,
            "risk": risk,
            "reasons": reasons,
        }
