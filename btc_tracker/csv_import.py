"""CSV importers — the no-API-keys path.

Supported files (auto-detected by header):
- Kraken trades export (History → Export → Trades): txid, pair, time, type,
  price, cost, fee, vol, ...
- Kraken ledgers export (History → Export → Ledgers): txid, refid, time,
  type, asset, amount, fee, ...
- Coinbase transaction statement (Statements → Generate → CSV): Timestamp,
  Transaction Type, Asset, Quantity Transacted, Subtotal,
  Total (inclusive of fees and/or spread), Fees and/or Spread, ...
"""

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from .costbasis import Tx
from .kraken import _is_btc_usd_pair


def import_file(path: str | Path) -> list[Tx]:
    path = Path(path)
    rows = _read_rows(path)
    if not rows:
        return []
    header = {h.strip().lower() for h in rows[0].keys()}
    if {"pair", "vol", "cost"} <= header:
        return _kraken_trades(rows)
    if {"refid", "asset", "amount"} <= header:
        return _kraken_ledgers(rows)
    if any("transaction type" in h for h in header):
        return _coinbase_statement(rows)
    raise ValueError(f"Unrecognized CSV format: {path.name}")


def _read_rows(path: Path) -> list[dict[str, str]]:
    """Read a CSV, skipping any preamble lines before the real header."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header_idx = 0
    for i, line in enumerate(lines[:30]):
        low = line.lower()
        if "txid" in low or "transaction type" in low:
            header_idx = i
            break
    reader = csv.DictReader(lines[header_idx:])
    return [
        {(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in reader
    ]


def _get(row: dict[str, str], *names: str) -> str:
    lowered = {k.lower(): v for k, v in row.items()}
    for name in names:
        for key, value in lowered.items():
            if key.startswith(name.lower()):
                return value
    return ""


def _parse_time(value: str) -> float:
    value = value.strip().replace("Z", "+00:00").replace("T", " ")
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
    ):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            continue
    raise ValueError(f"Unparseable timestamp: {value!r}")


def _num(value: str) -> float:
    cleaned = value.replace("$", "").replace(",", "").strip()
    return float(cleaned) if cleaned and cleaned != "-" else 0.0


def _kraken_trades(rows: list[dict[str, str]]) -> list[Tx]:
    txs: list[Tx] = []
    for row in rows:
        pair = _get(row, "pair")
        if not _is_btc_usd_pair(pair):
            continue
        is_buy = _get(row, "type") == "buy"
        cost, fee = _num(_get(row, "cost")), _num(_get(row, "fee"))
        txs.append(
            {
                "id": f"kraken:{_get(row, 'txid')}",
                "source": "kraken",
                "type": "buy" if is_buy else "sell",
                "timestamp": _parse_time(_get(row, "time")),
                "btc_amount": _num(_get(row, "vol")),
                "usd_amount": cost + fee if is_buy else cost - fee,
                "fee_usd": fee,
                "fee_btc": 0.0,
                "note": f"{pair} @ {_get(row, 'price')} (csv)",
            }
        )
    return txs


def _kraken_ledgers(rows: list[dict[str, str]]) -> list[Tx]:
    txs: list[Tx] = []
    for row in rows:
        asset = _get(row, "asset").upper().lstrip("XZ")
        ltype = _get(row, "type")
        if asset not in {"XBT", "BT", "BTC"} or ltype not in (
            "withdrawal",
            "deposit",
        ):
            continue
        txs.append(
            {
                "id": f"kraken:{_get(row, 'txid')}",
                "source": "kraken",
                "type": ltype,
                "timestamp": _parse_time(_get(row, "time")),
                "btc_amount": abs(_num(_get(row, "amount"))),
                "usd_amount": 0.0,
                "fee_usd": 0.0,
                "fee_btc": abs(_num(_get(row, "fee"))),
                "note": f"Kraken {ltype} (csv)",
            }
        )
    return txs


def _coinbase_statement(rows: list[dict[str, str]]) -> list[Tx]:
    txs: list[Tx] = []
    for row in rows:
        if _get(row, "asset").upper() != "BTC":
            continue
        raw_type = _get(row, "transaction type").lower()
        qty = abs(_num(_get(row, "quantity transacted")))
        total = abs(_num(_get(row, "total (inclusive", "total")))
        subtotal = abs(_num(_get(row, "subtotal")))
        fee = abs(_num(_get(row, "fees and/or spread", "fees")))
        when = _parse_time(_get(row, "timestamp"))
        # Stable synthetic id — Coinbase statements carry no transaction id.
        digest = hashlib.sha1(f"{when}:{raw_type}:{qty}:{total}".encode()).hexdigest()[
            :16
        ]
        base = {
            "id": f"coinbase:csv-{digest}",
            "source": "coinbase",
            "timestamp": when,
            "fee_usd": fee,
            "fee_btc": 0.0,
            "note": f"Coinbase {raw_type} (csv)",
        }
        if "buy" in raw_type:
            txs.append(
                {
                    **base,
                    "type": "buy",
                    "btc_amount": qty,
                    "usd_amount": total or subtotal,
                }
            )
        elif "sell" in raw_type:
            txs.append(
                {
                    **base,
                    "type": "sell",
                    "btc_amount": qty,
                    "usd_amount": (subtotal - fee) if subtotal else total,
                }
            )
        elif "send" in raw_type or "withdrawal" in raw_type:
            txs.append(
                {
                    **base,
                    "type": "withdrawal",
                    "btc_amount": qty,
                    "usd_amount": 0.0,
                    "fee_usd": 0.0,
                }
            )
        elif "receive" in raw_type or "deposit" in raw_type:
            txs.append(
                {
                    **base,
                    "type": "deposit",
                    "btc_amount": qty,
                    "usd_amount": 0.0,
                    "fee_usd": 0.0,
                }
            )
    return txs
