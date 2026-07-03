"""Cost-basis engine.

Normalized transaction shape (dict):
    id          unique string, stable across re-fetches (source-prefixed)
    source      "kraken" | "coinbase" | "manual"
    type        "buy" | "sell" | "withdrawal" | "deposit"
    timestamp   unix seconds (float)
    btc_amount  BTC quantity, always positive
    usd_amount  buys: total USD paid INCLUDING fees; sells: proceeds NET of
                fees; transfers: 0
    fee_usd     USD fee (informational; already included in usd_amount)
    fee_btc     BTC network/withdrawal fee (reduces holdings)
    note        free text

Method: **average cost**. Buys add to total cost; sells remove BTC at the
running average and realize the difference; withdrawals to self-custody are
NOT disposals — only the BTC network fee reduces holdings. This matches how
most portfolio trackers report "average cost", but is not tax advice.
"""

from datetime import datetime, timezone
from typing import Any

Tx = dict[str, Any]


def sort_txs(txs: list[Tx]) -> list[Tx]:
    return sorted(txs, key=lambda t: (t["timestamp"], t["id"]))


def compute(txs: list[Tx]) -> dict[str, Any]:
    """Run the average-cost engine over normalized transactions.

    Returns a summary dict plus a per-event timeline used by the charts.
    """
    btc = 0.0  # total BTC held (all locations)
    cost = 0.0  # USD cost basis of held BTC
    invested = 0.0  # lifetime USD in (buys, incl. fees)
    proceeds = 0.0  # lifetime USD out (sells, net of fees)
    realized = 0.0  # realized P&L from sells (average-cost method)
    fees_usd = 0.0
    fees_btc = 0.0
    location: dict[str, float] = {}  # venue -> BTC
    timeline: list[dict[str, Any]] = []
    events: list[Tx] = []

    for tx in sort_txs(txs):
        amt = float(tx.get("btc_amount", 0) or 0)
        usd = float(tx.get("usd_amount", 0) or 0)
        fee_b = float(tx.get("fee_btc", 0) or 0)
        fees_usd += float(tx.get("fee_usd", 0) or 0)
        venue = tx.get("source", "manual")

        if tx["type"] == "buy":
            btc += amt
            cost += usd
            invested += usd
            location[venue] = location.get(venue, 0.0) + amt
        elif tx["type"] == "sell":
            avg = cost / btc if btc > 0 else 0.0
            realized += usd - avg * amt
            proceeds += usd
            cost -= avg * amt
            btc -= amt
            location[venue] = location.get(venue, 0.0) - amt
        elif tx["type"] == "withdrawal":
            # Transfer to self-custody (Phantom): not a disposal.
            location[venue] = location.get(venue, 0.0) - (amt + fee_b)
            location["phantom"] = location.get("phantom", 0.0) + amt
            btc -= fee_b
            fees_btc += fee_b
            fee_b = 0.0
        elif tx["type"] == "deposit":
            # Assume a deposit is a transfer back from self-custody.
            moved = min(amt, max(location.get("phantom", 0.0), 0.0))
            location["phantom"] = location.get("phantom", 0.0) - moved
            location[venue] = location.get(venue, 0.0) + amt
            if moved < amt:
                # BTC from outside the tracked history — flag, don't invent basis.
                btc += amt - moved

        if fee_b:
            btc -= fee_b
            fees_btc += fee_b

        avg_cost = cost / btc if btc > 1e-12 else 0.0
        events.append(tx)
        timeline.append(
            {
                "date": datetime.fromtimestamp(
                    tx["timestamp"], tz=timezone.utc
                ).strftime("%Y-%m-%d"),
                "timestamp": tx["timestamp"],
                "type": tx["type"],
                "source": venue,
                "btc_amount": amt,
                "usd_amount": usd,
                "price": (usd / amt) if amt > 1e-12 and usd else None,
                "total_btc": btc,
                "avg_cost": avg_cost,
                "invested": invested,
            }
        )

    return {
        "total_btc": btc,
        "cost_basis": cost,
        "avg_cost": cost / btc if btc > 1e-12 else 0.0,
        "invested": invested,
        "proceeds": proceeds,
        "realized_pnl": realized,
        "fees_usd": fees_usd,
        "fees_btc": fees_btc,
        "location": {k: v for k, v in location.items() if abs(v) > 1e-10},
        "n_buys": sum(1 for t in events if t["type"] == "buy"),
        "n_sells": sum(1 for t in events if t["type"] == "sell"),
        "first_buy": next((e["date"] for e in timeline if e["type"] == "buy"), None),
        "timeline": timeline,
    }
