"""On-chain balance lookup for self-custody (Phantom) BTC addresses.

Uses the public mempool.space API — addresses are public information, no
key needed. Used to cross-check the computed Phantom balance against what
is actually on-chain.
"""

import time

import requests


def address_balance_btc(address: str) -> float:
    resp = requests.get(f"https://mempool.space/api/address/{address}", timeout=20)
    resp.raise_for_status()
    stats = resp.json()["chain_stats"]
    sats = stats["funded_txo_sum"] - stats["spent_txo_sum"]
    return sats / 1e8


def total_balance_btc(addresses: list[str]) -> float | None:
    """Sum of on-chain balances, or None if no addresses / all lookups fail."""
    if not addresses:
        return None
    total = 0.0
    ok = False
    for addr in addresses:
        try:
            total += address_balance_btc(addr)
            ok = True
        except Exception:
            pass
        time.sleep(0.3)
    return total if ok else None
