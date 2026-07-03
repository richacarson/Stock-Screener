"""Coinbase API client using a CDP API key (JWT auth) — read-only.

Create the key at https://portal.cdp.coinbase.com/access/api with
**View (read-only)** permission and download the JSON key file.

Uses the v2 accounts/transactions API, which covers both regular Coinbase
buys (including old recurring buys) and Advanced Trade fills, plus sends.
"""

import secrets
import time
from typing import Any

import jwt
import requests

from .costbasis import Tx

API_HOST = "api.coinbase.com"


def _build_jwt(key_name: str, private_key: str, method: str, path: str) -> str:
    now = int(time.time())
    payload = {
        "sub": key_name,
        "iss": "cdp",
        "nbf": now,
        "exp": now + 120,
        "uri": f"{method} {API_HOST}{path}",
    }
    return jwt.encode(
        payload,
        private_key,
        algorithm="ES256",
        headers={"kid": key_name, "nonce": secrets.token_hex(16)},
    )


def _get(key_name: str, private_key: str, path: str) -> dict[str, Any]:
    # The JWT uri claim must not include the query string.
    base_path = path.split("?")[0]
    token = _build_jwt(key_name, private_key, "GET", base_path)
    resp = requests.get(
        f"https://{API_HOST}{path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _paginate(key_name: str, private_key: str, path: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    next_path: str | None = path
    while next_path:
        body = _get(key_name, private_key, next_path)
        items.extend(body.get("data", []))
        next_path = (body.get("pagination") or {}).get("next_uri")
        if next_path:
            time.sleep(0.4)
    return items


def _btc_accounts(key_name: str, private_key: str) -> list[str]:
    accounts = _paginate(key_name, private_key, "/v2/accounts?limit=100")
    return [a["id"] for a in accounts if (a.get("currency") or {}).get("code") == "BTC"]


def _normalize(raw: dict[str, Any]) -> Tx | None:
    """Map a Coinbase v2 transaction to a normalized tx, or None to skip."""
    btc = float((raw.get("amount") or {}).get("amount") or 0)
    usd = abs(float((raw.get("native_amount") or {}).get("amount") or 0))
    ttype = raw.get("type", "")
    created = raw.get("created_at", "")
    ts = _parse_iso(created)
    base = {
        "id": f"coinbase:{raw['id']}",
        "source": "coinbase",
        "timestamp": ts,
        "fee_usd": 0.0,
        "fee_btc": 0.0,
        "note": (raw.get("details") or {}).get("title", ttype),
    }

    if ttype in ("buy", "advanced_trade_fill", "trade") and btc > 0:
        return {**base, "type": "buy", "btc_amount": btc, "usd_amount": usd}
    if ttype in ("sell", "advanced_trade_fill", "trade") and btc < 0:
        return {**base, "type": "sell", "btc_amount": -btc, "usd_amount": usd}
    if ttype == "send":
        kind = "withdrawal" if btc < 0 else "deposit"
        return {**base, "type": kind, "btc_amount": abs(btc), "usd_amount": 0.0}
    return None


def _parse_iso(value: str) -> float:
    from datetime import datetime, timezone

    if not value:
        return 0.0
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).timestamp()


def fetch_all(key_name: str, private_key: str) -> list[Tx]:
    txs: list[Tx] = []
    for account_id in _btc_accounts(key_name, private_key):
        raw_txs = _paginate(
            key_name,
            private_key,
            f"/v2/accounts/{account_id}/transactions?limit=100",
        )
        for raw in raw_txs:
            tx = _normalize(raw)
            if tx:
                txs.append(tx)
    return txs
