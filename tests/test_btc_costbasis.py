"""Tests for the BTC cost-basis engine and CSV importers."""

from btc_tracker import costbasis
from btc_tracker.csv_import import _coinbase_statement, _kraken_trades


def _buy(i: int, ts: float, btc: float, usd: float) -> dict:
    return {
        "id": f"t{i}", "source": "kraken", "type": "buy", "timestamp": ts,
        "btc_amount": btc, "usd_amount": usd, "fee_usd": 0.0, "fee_btc": 0.0,
        "note": "",
    }


def test_average_cost_two_buys():
    s = costbasis.compute([_buy(1, 100, 1.0, 30000), _buy(2, 200, 1.0, 50000)])
    assert s["total_btc"] == 2.0
    assert s["avg_cost"] == 40000
    assert s["invested"] == 80000
    assert s["realized_pnl"] == 0


def test_sell_realizes_at_average():
    txs = [
        _buy(1, 100, 1.0, 30000),
        _buy(2, 200, 1.0, 50000),
        {
            "id": "s1", "source": "kraken", "type": "sell", "timestamp": 300,
            "btc_amount": 0.5, "usd_amount": 25000, "fee_usd": 0.0,
            "fee_btc": 0.0, "note": "",
        },
    ]
    s = costbasis.compute(txs)
    # Sold 0.5 at $50k proceeds vs $40k avg cost -> +$5,000 realized.
    assert round(s["realized_pnl"]) == 5000
    assert s["total_btc"] == 1.5
    # Average cost of the remainder is unchanged by an average-cost sale.
    assert round(s["avg_cost"]) == 40000
    assert round(s["cost_basis"]) == 60000


def test_withdrawal_to_phantom_is_not_a_disposal():
    txs = [
        _buy(1, 100, 1.0, 40000),
        {
            "id": "w1", "source": "kraken", "type": "withdrawal",
            "timestamp": 200, "btc_amount": 0.5, "usd_amount": 0.0,
            "fee_usd": 0.0, "fee_btc": 0.0001, "note": "",
        },
    ]
    s = costbasis.compute(txs)
    assert s["realized_pnl"] == 0
    assert abs(s["total_btc"] - 0.9999) < 1e-9  # only the network fee left
    assert abs(s["location"]["phantom"] - 0.5) < 1e-9
    assert abs(s["location"]["kraken"] - 0.4999) < 1e-9
    # Cost basis unchanged; avg cost ticks up slightly from the fee.
    assert round(s["cost_basis"]) == 40000
    assert s["avg_cost"] > 40000


def test_timeline_tracks_running_average():
    s = costbasis.compute([_buy(1, 100, 0.5, 10000), _buy(2, 200, 0.5, 30000)])
    assert [round(e["avg_cost"]) for e in s["timeline"]] == [20000, 40000]


def test_kraken_trades_csv_buy_includes_fee():
    rows = [{
        "txid": "TX1", "pair": "XXBTZUSD", "time": "2024-01-05 12:00:00",
        "type": "buy", "price": "40000", "cost": "400.00", "fee": "1.60",
        "vol": "0.01",
    }]
    txs = _kraken_trades(rows)
    assert len(txs) == 1
    assert txs[0]["usd_amount"] == 401.60
    assert txs[0]["btc_amount"] == 0.01


def test_coinbase_statement_csv():
    rows = [
        {
            "Timestamp": "2021-02-01 10:00:00", "Transaction Type": "Buy",
            "Asset": "BTC", "Quantity Transacted": "0.002",
            "Subtotal": "$98.01", "Total (inclusive of fees and/or spread)": "$100.00",
            "Fees and/or Spread": "$1.99",
        },
        {
            "Timestamp": "2021-03-01 10:00:00", "Transaction Type": "Send",
            "Asset": "BTC", "Quantity Transacted": "0.002", "Subtotal": "",
            "Total (inclusive of fees and/or spread)": "", "Fees and/or Spread": "",
        },
        {
            "Timestamp": "2021-03-02 10:00:00", "Transaction Type": "Buy",
            "Asset": "ETH", "Quantity Transacted": "1.0",
            "Subtotal": "$1000", "Total (inclusive of fees and/or spread)": "$1010",
            "Fees and/or Spread": "$10",
        },
    ]
    txs = _coinbase_statement(rows)
    assert len(txs) == 2  # ETH row skipped
    assert txs[0]["type"] == "buy" and txs[0]["usd_amount"] == 100.00
    assert txs[1]["type"] == "withdrawal"


def test_dedupe_ids_are_stable():
    rows = [{
        "Timestamp": "2021-02-01 10:00:00", "Transaction Type": "Buy",
        "Asset": "BTC", "Quantity Transacted": "0.002",
        "Subtotal": "$98.01", "Total (inclusive of fees and/or spread)": "$100.00",
        "Fees and/or Spread": "$1.99",
    }]
    assert _coinbase_statement(rows)[0]["id"] == _coinbase_statement(rows)[0]["id"]
