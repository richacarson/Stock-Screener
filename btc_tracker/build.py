"""Build the private BTC dashboard HTML from stored transactions."""

import json
from datetime import datetime, timezone
from typing import Any

from jinja2 import Environment, FileSystemLoader

from . import config, costbasis, onchain, prices, store


def _chart_data(summary: dict[str, Any], history: list[dict[str, Any]]) -> str:
    timeline = summary["timeline"]
    trade_events = [t for t in timeline if t["type"] in ("buy", "sell")]
    # Clip the price backdrop to the user's own history.
    start = trade_events[0]["timestamp"] if trade_events else 0
    now_point: list[dict[str, float]] = []
    data = {
        "avg_cost": [
            {"t": t["timestamp"], "v": round(t["avg_cost"], 2)} for t in trade_events
        ],
        "total_btc": [
            {"t": t["timestamp"], "v": round(t["total_btc"], 8)} for t in timeline
        ],
        "buys": [
            {"t": t["timestamp"], "v": round(t["price"], 2)}
            for t in trade_events
            if t["type"] == "buy" and t["price"]
        ],
        "price_history": [
            {"t": h["timestamp"], "v": round(h["close"], 2)}
            for h in history
            if h["timestamp"] >= start - 86400 * 14
        ]
        + now_point,
    }
    return json.dumps(data)


def build(skip_network: bool = False) -> str:
    """Render the dashboard. Returns the output path as a string."""
    txs = store.load()
    summary = costbasis.compute(txs)

    spot = 0.0
    history: list[dict[str, Any]] = []
    onchain_total: float | None = None
    if not skip_network:
        try:
            spot = prices.spot_price()
        except Exception:
            spot = 0.0
        history = prices.weekly_history()
        onchain_total = onchain.total_balance_btc(config.phantom_addresses())
    if not spot:
        # Fall back to the user's average cost so the page still renders.
        spot = summary["avg_cost"] or 1.0

    current_value = summary["total_btc"] * spot
    unrealized = current_value - summary["cost_basis"]
    unrealized_pct = (
        100 * unrealized / summary["cost_basis"] if summary["cost_basis"] else 0.0
    )
    phantom_computed = summary["location"].get("phantom", 0.0)
    onchain_mismatch = (
        onchain_total is not None and abs(onchain_total - phantom_computed) > 0.0001
    )

    env = Environment(
        loader=FileSystemLoader(config.REPO_ROOT / "templates"), autoescape=True
    )
    template = env.get_template("btc_dashboard.html")
    html = template.render(
        s=summary,
        spot=spot,
        current_value=current_value,
        unrealized=unrealized,
        unrealized_pct=unrealized_pct,
        locations=sorted(summary["location"].items(), key=lambda kv: -kv[1]),
        onchain=onchain_total,
        onchain_mismatch=onchain_mismatch,
        phantom_computed=phantom_computed,
        txs=list(reversed(summary["timeline"])),
        chart_data=_chart_data(summary, history),
        built_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )
    config.DASHBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.DASHBOARD_FILE.write_text(html)
    return str(config.DASHBOARD_FILE)
