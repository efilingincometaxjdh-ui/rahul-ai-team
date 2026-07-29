# ============================================================
# RAHUL AI TEAM
# AGENT 05 — PERMISSION ENGINE
# Final deterministic safety gate
# ============================================================


class PermissionEngine:
    VALID_RISKS = {"LOW", "MEDIUM", "HIGH", "EXTREME"}
    VALID_STATES = {
        "STRONG_BULLISH", "BULLISH", "NEUTRAL", "BEARISH", "STRONG_BEARISH", "NO_TRADE"
    }

    def __init__(self, minimum_confidence=55):
        self.minimum_confidence = minimum_confidence

    def evaluate(self, decision):
        """Convert Agent 04 output into a fail-closed trading permission."""
        if not isinstance(decision, dict):
            return {"permission": "BLOCK_TRADING", "reason": "Invalid decision state."}

        state = str(decision.get("decision", "NO_TRADE")).upper()
        risk = str(decision.get("risk", "EXTREME")).upper()
        try:
            confidence = int(decision.get("confidence", 0))
        except (TypeError, ValueError):
            confidence = 0

        if state not in self.VALID_STATES:
            return {"permission": "BLOCK_TRADING", "reason": "Unknown decision state."}
        if risk not in self.VALID_RISKS:
            return {"permission": "BLOCK_TRADING", "reason": "Unknown risk state."}
        if state == "NO_TRADE":
            return {"permission": "BLOCK_TRADING", "reason": "Decision engine blocked trading."}
        if risk == "EXTREME":
            return {"permission": "BLOCK_TRADING", "reason": "Extreme news risk."}
        if not 0 <= confidence <= 100:
            return {"permission": "BLOCK_TRADING", "reason": "Invalid decision confidence."}
        if confidence < self.minimum_confidence:
            return {
                "permission": "CAUTION",
                "reason": f"Decision confidence {confidence}% is below {self.minimum_confidence}%.",
            }

        mapping = {
            "STRONG_BULLISH": ("ALLOW_BUYS", "Strong bullish environment."),
            "BULLISH": ("ALLOW_BUYS", "Bullish environment."),
            "NEUTRAL": ("ALLOW_BOTH", "Neutral market."),
            "BEARISH": ("ALLOW_SELLS", "Bearish environment."),
            "STRONG_BEARISH": ("ALLOW_SELLS", "Strong bearish environment."),
        }
        permission, reason = mapping[state]
        return {"permission": permission, "reason": reason}
