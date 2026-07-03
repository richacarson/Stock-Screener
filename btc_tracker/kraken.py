"""Kraken private API client — read-only endpoints only.

Requires an API key with permissions: Query Funds, Query Closed Orders &
Trades, Query Ledger Entries. No trading or withdrawal permissions needed.
"""

import base64
import hashlib
import hmac
import time
import urllib.parse
from typing import Any

import requests

from .costbasis import Tx

API_URL = "https://api.kraken.com"

# Kraken names BTC "XBT"/"XXBT"; accept USD and USDT quotes.
_BTC_ALIASES = {"XBT", "XXBT", "BTC"}
_USD_QUOTES = {"USD", "ZUSD", "USDT"}


def _sign(path: str, data: dict[str, Any], secret: str) -> str:
    postdata = urllib.parse.urlencode(data)
    message = (
        path.encode()
        + hashlib.sha256((str(data["nonce"]) + postdata).encode()).digest()
    )
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()


def _private(path: str, key: str, secret: str, **params: Any) -> dict[str, Any]:
    data: dict[str, Any] = {"nonce": int(time.time() * 1000000), **params}
    headers = {"API-Key": key, "API-Sign": _sign(path, data, secret)}
    resp = requests.post(API_URL + path, headers=headers, data=data, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    if body.get("error"):
        raise RuntimeError(f"Kraken API error: {body['error']}")
    return body["result"]


def _is_btc_usd_pair(pair: str) -> bool:
    p = pair.upper()
    return any(p.startswith(b) for b in _BTC_ALIASES) and any(
        p.endswith(q) for q in _USD_QUOTES
    )


def fetch_trades(key: str, secret: str) -> list[Tx]:
    """All BTC/USD spot trades, paginated 50 at a time."""
    txs: list[Tx] = []
    offset = 0
    while True:
        result = _private("/0/private/TradesHistory", key, secret, ofs=offset)
        trades = result.get("trades", {})
        for txid, t in trades.items():
            if not _is_btc_usd_pair(t["pair"]):
                continue
            vol = float(t["vol"])
            cost = float(t["cost"])
            fee = float(t["fee"])
            is_buy = t["type"] == "buy"
            txs.append(
                {
                    "id": f"kraken:{txid}",
                    "source": "kraken",
                    "type": "buy" if is_buy else "sell",
                    "timestamp": float(t["time"]),
                    "btc_amount": vol,
                    # buys: cost + fee (all-in); sells: proceeds net of fee
                    "usd_amount": cost + fee if is_buy else cost - fee,
                    "fee_usd": fee,
                    "fee_btc": 0.0,
                    "note": f"{t['pair']} @ {t['price']}",
                }
            )
        offset += len(trades)
        if offset >= int(result.get("count", 0)) or not trades:
            break
        time.sleep(1)  # respect rate limits
    return txs


def fetch_transfers(key: str, secret: str) -> list[Tx]:
    """BTC deposits and withdrawals from the ledger (Phantom transfers)."""
    txs: list[Tx] = []
    for ledger_type in ("withdrawal", "deposit"):
        offset = 0
        while True:
            result = _private(
                "/0/private/Ledgers",
                key,
                secret,
                asset="XBT",
                type=ledger_type,
                ofs=offset,
            )
            entries = result.get("ledger", {})
            for lid, e in entries.items():
                if e["asset"].upper().lstrip("XZ") not in {"XBT", "BT", "BTC"}:
                    continue
                amount = abs(float(e["amount"]))
                fee = abs(float(e.get("fee", 0)))
                txs.append(
                    {
                        "id": f"kraken:{lid}",
                        "source": "kraken",
                        "type": ledger_type,
                        "timestamp": float(e["time"]),
                        "btc_amount": amount,
                        "usd_amount": 0.0,
                        "fee_usd": 0.0,
                        "fee_btc": fee,
                        "note": f"Kraken {ledger_type} (ref {e.get('refid', '')})",
                    }
                )
            offset += len(entries)
            if offset >= int(result.get("count", 0)) or not entries:
                break
            time.sleep(1)
    return txs


def fetch_all(key: str, secret: str) -> list[Tx]:
    return fetch_trades(key, secret) + fetch_transfers(key, secret)
