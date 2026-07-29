# Rahul AI Team

A ₹0-first modular automation project. The first production component is **Agent 02**, which builds a multi-timeframe XAUUSD technical market state for later intelligence agents to consume.

## Agent 02 — XAUUSD Market Intelligence

Agent 02 requests 100 candles for M5, M15, H1 and H4 from Twelve Data, then calculates EMA20, EMA50, RSI14, ATR14, ADX14 and basic market structure. It writes a normalized state to `data/current/agent02.json`.

Health values:

- `SUCCESS` — all requested timeframes produced usable analysis.
- `DEGRADED` — at least one timeframe worked, but some data/analysis failed.
- `FAILED` — no usable timeframe state was produced.

## Configuration

Agent 02 requires one environment variable:

`TWELVE_DATA_API_KEY`

For GitHub Actions, store it as a repository Actions secret with the same name. Never commit the key.

## Run locally

```bash
python agent02.py
```

No third-party Python package is currently required.

## Tests

```bash
python -m unittest discover -s tests -v
```

The `Tests` GitHub Actions workflow runs automatically on pushes and pull requests.

## Automation

`.github/workflows/agent02.yml` supports manual execution and is scheduled every four hours on weekdays. Each run uploads `agent02.json` as a short-lived workflow artifact so the generated state can be inspected without committing frequently changing market data to the repository.

## Project direction

The repository is being built as modular intelligence infrastructure rather than an auto-trading system. Future agents can read normalized state through `utils/json_reader.py` and combine technical, news and macro information before any downstream decision/alert layer is added.
