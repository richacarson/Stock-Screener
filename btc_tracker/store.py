"""Persistent store for normalized transactions.

Everything lives in data/btc_transactions.json (gitignored — personal data).
Transactions are deduped by their stable `id`, so re-fetching from the APIs
or re-importing a CSV is always safe.
"""

import json
from typing import Any

from .config import MANUAL_FILE, TRANSACTIONS_FILE
from .costbasis import Tx, sort_txs


def load() -> list[Tx]:
    txs: list[Tx] = []
    if TRANSACTIONS_FILE.exists():
        txs = json.loads(TRANSACTIONS_FILE.read_text())
    if MANUAL_FILE.exists():
        manual = json.loads(MANUAL_FILE.read_text())
        known = {t["id"] for t in txs}
        txs += [t for t in manual if t["id"] not in known]
    return sort_txs(txs)


def merge(new_txs: list[Tx]) -> tuple[int, int]:
    """Merge new transactions into the store. Returns (added, total)."""
    existing: dict[str, Tx] = {}
    if TRANSACTIONS_FILE.exists():
        for t in json.loads(TRANSACTIONS_FILE.read_text()):
            existing[t["id"]] = t
    added = 0
    for t in new_txs:
        if t["id"] not in existing:
            added += 1
        existing[t["id"]] = t
    merged = sort_txs(list(existing.values()))
    TRANSACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRANSACTIONS_FILE.write_text(json.dumps(merged, indent=2))
    return added, len(merged)


def add_manual(tx: Tx) -> None:
    manual: list[Tx] = []
    if MANUAL_FILE.exists():
        manual = json.loads(MANUAL_FILE.read_text())
    manual.append(tx)
    MANUAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    MANUAL_FILE.write_text(json.dumps(sort_txs(manual), indent=2))


def summary_counts(txs: list[Tx]) -> dict[str, Any]:
    by_source: dict[str, int] = {}
    for t in txs:
        by_source[t["source"]] = by_source.get(t["source"], 0) + 1
    return by_source
