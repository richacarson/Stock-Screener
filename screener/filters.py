"""Stock screening filters — IOWN-aligned criteria.

Relaxed to allow high-growth innovation stocks that may have elevated P/E
ratios or temporarily negative revenue growth during reinvestment phases.
"""


# Default screening criteria
DEFAULT_CRITERIA = {
    "min_market_cap": 1_000_000_000,      # $1B minimum
    "min_avg_volume": 500_000,             # 500K average daily volume
    "pe_range": (0, 200),                  # Widened — high-growth stocks often have elevated P/E
    "min_revenue_growth": -0.10,           # Allow up to -10% — reinvestment phases
    "above_sma_50": False,                 # Disabled — Social Arbitrage may find undervalued dips
}


def apply_filters(
    stocks: list[dict],
    criteria: dict | None = None,
) -> list[dict]:
    """Apply screening filters to a list of stocks.

    Args:
        stocks: List of stock data dicts from fetcher.
        criteria: Override default criteria. Keys match DEFAULT_CRITERIA.

    Returns:
        List of stocks that pass all filters.
    """
    c = {**DEFAULT_CRITERIA, **(criteria or {})}
    passed = []

    for stock in stocks:
        if not _passes_all(stock, c):
            continue
        passed.append(stock)

    return passed


def _passes_all(stock: dict, criteria: dict) -> bool:
    """Check if a stock passes all criteria."""
    market_cap = stock.get("market_cap")
    if market_cap is None or market_cap < criteria["min_market_cap"]:
        return False

    avg_volume = stock.get("avg_volume")
    if avg_volume is None or avg_volume < criteria["min_avg_volume"]:
        return False

    pe = stock.get("pe_ratio")
    if pe is not None:
        pe_min, pe_max = criteria["pe_range"]
        if pe < pe_min or pe > pe_max:
            return False

    rev_growth = stock.get("revenue_growth")
    if rev_growth is not None and rev_growth < criteria["min_revenue_growth"]:
        return False

    if criteria.get("above_sma_50"):
        price = stock.get("price")
        sma_50 = stock.get("sma_50")
        if price is not None and sma_50 is not None and price < sma_50:
            return False

    return True
