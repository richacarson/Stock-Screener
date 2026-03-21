"""Stock ranking and scoring logic."""


def rank_stocks(stocks: list[dict]) -> list[dict]:
    """Score and rank stocks that passed filtering.

    Composite score based on:
    - Revenue growth (30%)
    - Relative strength vs 50-day SMA (25%)
    - Volume trend (20%)
    - P/E attractiveness (25%)

    Returns:
        Stocks sorted by composite score (highest first).
    """
    scored = []
    for stock in stocks:
        score = _composite_score(stock)
        scored.append({**stock, "score": round(score, 2)})

    scored.sort(key=lambda s: s["score"], reverse=True)
    return scored


def _composite_score(stock: dict) -> float:
    """Calculate composite score for a stock."""
    score = 0.0

    # Revenue growth component (30%)
    rev_growth = stock.get("revenue_growth", 0) or 0
    score += min(rev_growth * 100, 50) * 0.30  # Cap at 50% growth

    # Relative strength vs SMA (25%)
    price = stock.get("price", 0)
    sma_50 = stock.get("sma_50", 0)
    if sma_50 and sma_50 > 0:
        rs = ((price - sma_50) / sma_50) * 100
        score += min(max(rs, 0), 30) * 0.25  # Cap at 30% above SMA

    # Volume trend (20%)
    avg_vol = stock.get("avg_volume", 0)
    recent_vol = stock.get("recent_volume", avg_vol)
    if avg_vol and avg_vol > 0:
        vol_ratio = recent_vol / avg_vol
        score += min(vol_ratio * 10, 20) * 0.20

    # P/E attractiveness (25%) — lower is better within range
    pe = stock.get("pe_ratio")
    if pe and 5 <= pe <= 40:
        pe_score = (40 - pe) / 35 * 25  # Linear scale, lower PE = higher score
        score += pe_score * 0.25

    return score
