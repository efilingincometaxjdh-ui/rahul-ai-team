# RAHUL AI TEAM — GOLD-API.COM REFERENCE EVIDENCE ADAPTER

from history.reference_price import validate_reference_quote

PROVIDER = "gold-api.com"


def normalize_gold_api_xau(payload):
    """Normalize a gold-api.com XAU response into validated evidence.

    This adapter is deliberately transport-free: callers supply an already-fetched
    payload. It cannot make network requests, schedule collection, or affect
    trading authority.
    """
    if not isinstance(payload, dict):
        raise ValueError("gold-api payload must be a dictionary")
    if payload.get("symbol") != "XAU":
        raise ValueError("gold-api payload symbol must be XAU")

    # The public /price/XAU endpoint documents gold price in USD per troy ounce.
    # Require the provider timestamp rather than substituting local fetch time.
    observed_at = payload.get("updatedAt")
    if not isinstance(observed_at, str) or not observed_at.strip():
        raise ValueError("gold-api payload updatedAt is required")

    return validate_reference_quote(
        {
            "provider": PROVIDER,
            "symbol": "XAUUSD",
            "market": "SPOT",
            "quote_currency": "USD",
            "price": payload.get("price"),
            "observed_at": observed_at,
            "requires_credentials": False,
        }
    )
