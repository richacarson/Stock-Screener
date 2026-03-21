"""Data fetching from Yahoo Finance via yfinance."""

import yfinance as yf


def fetch_stock_data(tickers: list[str]) -> list[dict]:
    """Fetch fundamental and technical data for a list of tickers.

    Returns:
        List of dicts with stock data fields.
    """
    results = []

    # Batch download for efficiency
    data = yf.download(tickers, period="3mo", group_by="ticker", progress=False)

    for ticker in tickers:
        try:
            stock = _fetch_single(ticker, data)
            if stock:
                results.append(stock)
        except Exception as e:
            print(f"  Warning: Failed to fetch {ticker}: {e}")

    return results


def _fetch_single(ticker: str, price_data) -> dict | None:
    """Fetch data for a single ticker."""
    info = yf.Ticker(ticker)

    try:
        fast_info = info.fast_info
        hist = info.history(period="3mo")
    except Exception:
        return None

    if hist.empty:
        return None

    price = hist["Close"].iloc[-1] if not hist.empty else None
    sma_50 = hist["Close"].rolling(50).mean().iloc[-1] if len(hist) >= 50 else None
    avg_volume = hist["Volume"].mean() if not hist.empty else None
    recent_volume = hist["Volume"].iloc[-5:].mean() if len(hist) >= 5 else avg_volume

    try:
        info_dict = info.info
    except Exception:
        info_dict = {}

    return {
        "ticker": ticker,
        "name": info_dict.get("shortName", ticker),
        "price": round(float(price), 2) if price else None,
        "market_cap": fast_info.get("marketCap") if hasattr(fast_info, "get") else info_dict.get("marketCap"),
        "pe_ratio": info_dict.get("trailingPE"),
        "forward_pe": info_dict.get("forwardPE"),
        "revenue_growth": info_dict.get("revenueGrowth"),
        "profit_margin": info_dict.get("profitMargins"),
        "avg_volume": round(float(avg_volume)) if avg_volume else None,
        "recent_volume": round(float(recent_volume)) if recent_volume else None,
        "sma_50": round(float(sma_50), 2) if sma_50 else None,
        "sector": info_dict.get("sector", "Unknown"),
        "industry": info_dict.get("industry", "Unknown"),
    }
