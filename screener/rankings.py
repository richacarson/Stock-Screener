"""Stock ranking and scoring logic — IOWN Value-Aligned Framework.

Scores stocks across four dimensions reflecting IOWN's investment philosophy:
1. Return on Intention (Innovation / Inspiration / Infrastructure)
2. AI Disruption & Moat Strength
3. Infinite Game (long-term sustainability)
4. Social Arbitrage Signal (market inefficiency / momentum)
"""

# Sectors considered high-innovation for Return on Intention scoring
INNOVATION_SECTORS = {
    "Technology", "Communication Services", "Healthcare",
}

# Sectors aligned with infrastructure / energy transition
INFRASTRUCTURE_SECTORS = {
    "Utilities", "Industrials", "Energy", "Basic Materials",
}


def rank_stocks(stocks: list[dict]) -> list[dict]:
    """Score and rank stocks using IOWN's four-dimension framework.

    Each dimension scores 0–25 points, for a maximum composite of 100.

    Returns:
        Stocks sorted by composite score (highest first).
    """
    scored = []
    for stock in stocks:
        dimensions = _score_dimensions(stock)
        total = sum(dimensions.values())
        scored.append({
            **stock,
            "score": round(total, 2),
            "score_intention": round(dimensions["intention"], 2),
            "score_moat": round(dimensions["moat"], 2),
            "score_infinite": round(dimensions["infinite"], 2),
            "score_arbitrage": round(dimensions["arbitrage"], 2),
        })

    scored.sort(key=lambda s: s["score"], reverse=True)
    return scored


def _score_dimensions(stock: dict) -> dict[str, float]:
    """Calculate all four IOWN dimension scores for a stock."""
    return {
        "intention": _score_intention(stock),
        "moat": _score_moat(stock),
        "infinite": _score_infinite(stock),
        "arbitrage": _score_arbitrage(stock),
    }


def _score_intention(stock: dict) -> float:
    """Return on Intention — Innovation, Inspiration, Infrastructure.

    Rewards: high revenue growth, forward-looking valuation compression
    (forward PE < trailing PE = market expects growth), and alignment
    with innovation/infrastructure sectors.
    """
    score = 0.0

    # Revenue growth as innovation signal (0–10 pts)
    rev_growth = stock.get("revenue_growth", 0) or 0
    score += min(rev_growth * 100, 40) * 0.25  # Cap at 40% → 10 pts

    # Forward PE discount vs trailing PE (0–7 pts)
    # If forward PE < trailing PE, the market expects earnings to grow
    pe = stock.get("pe_ratio")
    fwd_pe = stock.get("forward_pe")
    if pe and fwd_pe and pe > 0 and fwd_pe > 0:
        pe_compression = (pe - fwd_pe) / pe
        score += min(max(pe_compression, 0), 0.5) * 14  # Cap at 50% compression → 7 pts

    # Sector alignment (0–8 pts)
    sector = stock.get("sector", "")
    if sector in INNOVATION_SECTORS:
        score += 8
    elif sector in INFRASTRUCTURE_SECTORS:
        score += 5

    return min(score, 25)


def _score_moat(stock: dict) -> float:
    """AI Disruption & Moat Strength.

    Rewards: high profit margins (pricing power), strong return on equity
    (efficient capital deployment), and large market cap (dominant position).
    """
    score = 0.0

    # Profit margin as pricing power signal (0–10 pts)
    margin = stock.get("profit_margin", 0) or 0
    score += min(max(margin * 100, 0), 40) * 0.25  # Cap at 40% margin → 10 pts

    # Return on equity (0–8 pts)
    roe = stock.get("return_on_equity", 0) or 0
    score += min(max(roe * 100, 0), 40) * 0.20  # Cap at 40% ROE → 8 pts

    # Market cap dominance (0–7 pts) — log scale
    market_cap = stock.get("market_cap", 0) or 0
    if market_cap >= 1_000_000_000_000:  # $1T+
        score += 7
    elif market_cap >= 200_000_000_000:  # $200B+
        score += 5
    elif market_cap >= 50_000_000_000:  # $50B+
        score += 3
    elif market_cap >= 10_000_000_000:  # $10B+
        score += 1.5

    return min(score, 25)


def _score_infinite(stock: dict) -> float:
    """Infinite Game — long-term sustainability (Simon Sinek).

    Rewards: positive margins (sustainable business), low debt (financial
    resilience), and earnings growth (compounding over time).
    """
    score = 0.0

    # Positive profit margin = sustainable model (0–8 pts)
    margin = stock.get("profit_margin", 0) or 0
    if margin > 0.20:
        score += 8
    elif margin > 0.10:
        score += 6
    elif margin > 0.05:
        score += 4
    elif margin > 0:
        score += 2

    # Low debt-to-equity = financial resilience (0–9 pts)
    dte = stock.get("debt_to_equity")
    if dte is not None:
        if dte < 30:
            score += 9
        elif dte < 60:
            score += 7
        elif dte < 100:
            score += 5
        elif dte < 150:
            score += 3
        else:
            score += 1
    else:
        score += 4  # Unknown debt — neutral

    # Earnings growth = compounding (0–8 pts)
    eg = stock.get("earnings_growth", 0) or 0
    score += min(max(eg * 100, 0), 40) * 0.20  # Cap at 40% → 8 pts

    return min(score, 25)


def _score_arbitrage(stock: dict) -> float:
    """Social Arbitrage Signal (Chris Camillo).

    Rewards: volume surge (social/retail interest), price momentum
    above SMA-50 (trend confirmation), and forward PE discount
    (market hasn't fully priced in the opportunity).
    """
    score = 0.0

    # Volume surge — recent vs average (0–10 pts)
    avg_vol = stock.get("avg_volume", 0) or 0
    recent_vol = stock.get("recent_volume", 0) or 0
    if avg_vol > 0:
        vol_ratio = recent_vol / avg_vol
        if vol_ratio >= 2.0:
            score += 10
        elif vol_ratio >= 1.5:
            score += 8
        elif vol_ratio >= 1.2:
            score += 5
        elif vol_ratio >= 1.0:
            score += 3
        else:
            score += 1

    # Price momentum vs SMA-50 (0–8 pts)
    price = stock.get("price", 0)
    sma_50 = stock.get("sma_50", 0)
    if sma_50 and sma_50 > 0:
        rs = ((price - sma_50) / sma_50) * 100
        score += min(max(rs, 0), 20) * 0.40  # Cap at 20% above → 8 pts

    # Forward PE discount = market hasn't priced it in (0–7 pts)
    pe = stock.get("pe_ratio")
    fwd_pe = stock.get("forward_pe")
    if pe and fwd_pe and pe > 0 and fwd_pe > 0 and fwd_pe < pe:
        discount = (pe - fwd_pe) / pe
        score += min(discount, 0.5) * 14  # Cap at 50% discount → 7 pts

    return min(score, 25)
