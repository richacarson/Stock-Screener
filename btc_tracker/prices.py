"""Public (no-auth) BTC price data."""

from typing import Any

import requests


def spot_price() -> float:
    """Current BTC/USD price. Kraken public ticker, Coinbase fallback."""
    try:
        resp = requests.get(
            "https://api.kraken.com/0/public/Ticker?pair=XBTUSD", timeout=15
        )
        resp.raise_for_status()
        result = resp.json()["result"]
        return float(next(iter(result.values()))["c"][0])
    except Exception:
        resp = requests.get(
            "https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=15
        )
        resp.raise_for_status()
        return float(resp.json()["data"]["amount"])


def weekly_history() -> list[dict[str, Any]]:
    """Weekly BTC/USD closes (up to ~13 years) for the chart backdrop.

    Returns [{"timestamp": ..., "close": ...}], or [] on failure — the
    dashboard degrades gracefully without it.
    """
    try:
        resp = requests.get(
            "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=10080",
            timeout=20,
        )
        resp.raise_for_status()
        body = resp.json()
        candles = next(v for k, v in body["result"].items() if k != "last")
        return [{"timestamp": float(c[0]), "close": float(c[4])} for c in candles]
    except Exception:
        return []
