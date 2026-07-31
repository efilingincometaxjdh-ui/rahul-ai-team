# RAHUL AI TEAM — REFERENCE PRICE EVIDENCE CONTRACT

import math
from datetime import datetime


REFERENCE_SYMBOL = "XAUUSD"
REFERENCE_MARKET = "SPOT"
REFERENCE_QUOTE_CURRENCY = "USD"


def _parse_timestamp(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("observed_at must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("observed_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("observed_at must include timezone information")
    return value


def validate_reference_quote(quote):
    """Validate price evidence before it can be used by a future outcome collector.

    The contract deliberately requires spot XAUUSD. Futures, ETFs, synthetic proxies,
    credential-bearing execution feeds, and unknown instruments are not silently
    treated as XAUUSD outcomes.
    """
    if not isinstance(quote, dict):
        raise ValueError("reference quote must be a dictionary")
    if quote.get("symbol") != REFERENCE_SYMBOL:
        raise ValueError("reference quote symbol must be XAUUSD")
    if quote.get("market") != REFERENCE_MARKET:
        raise ValueError("reference quote market must be SPOT")
    if quote.get("quote_currency") != REFERENCE_QUOTE_CURRENCY:
        raise ValueError("reference quote currency must be USD")
    provider = quote.get("provider")
    if not isinstance(provider, str) or not provider.strip():
        raise ValueError("reference quote provider is required")
    if quote.get("requires_credentials") is not False:
        raise ValueError("Phase 2 reference source must not require credentials")
    price = quote.get("price")
    if isinstance(price, bool) or not isinstance(price, (int, float)) or not math.isfinite(price) or price <= 0:
        raise ValueError("reference quote price must be a finite positive number")
    observed_at = _parse_timestamp(quote.get("observed_at"))
    return {
        "provider": provider.strip(),
        "symbol": REFERENCE_SYMBOL,
        "market": REFERENCE_MARKET,
        "quote_currency": REFERENCE_QUOTE_CURRENCY,
        "price": float(price),
        "observed_at": observed_at,
        "requires_credentials": False,
    }
