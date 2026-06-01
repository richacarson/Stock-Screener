"""Pre-compute infrastructure scores and full financial data for screening agents."""
import sys, json, csv, os
sys.path.insert(0, '/home/user/Stock-Screener')
import yfinance as yf

def get_full_data(ticker):
    """Get comprehensive financial data from yfinance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="3mo")

        price = round(float(hist["Close"].iloc[-1]), 2) if not hist.empty else None
        avg_vol = round(float(hist["Volume"].mean())) if not hist.empty else None

        div_yield = info.get('dividendYield')
        payout = info.get('payoutRatio')
        peg = info.get('pegRatio') or info.get('trailingPegRatio')

        return {
            'name': info.get('shortName', ticker),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'exchange': info.get('exchange', ''),
            'country': info.get('country', 'United States'),
            'website': info.get('website', ''),
            'employees': info.get('fullTimeEmployees'),
            'description': info.get('longBusinessSummary', ''),
            'stock_price': price,
            'pe_ratio': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'peg_ratio': peg,
            'debt_to_equity': info.get('debtToEquity'),
            'return_on_equity': info.get('returnOnEquity'),
            'profit_margin': info.get('profitMargins'),
            'revenue_growth_yoy': info.get('revenueGrowth'),
            'earnings_growth': info.get('earningsGrowth'),
            'avg_daily_volume': avg_vol,
            'dividend_yield': div_yield,
            'payout_ratio': payout,
            'market_cap': info.get('marketCap'),
        }
    except Exception as e:
        return {'error': str(e), 'name': ticker}


def calc_infrastructure(d, sleeve):
    """Calculate infrastructure score mechanically per SCREENING.md."""
    price = d.get('stock_price') or 0
    vol = d.get('avg_daily_volume') or 0
    if price * vol < 1_000_000:
        return 0, "LIQUIDITY FLOOR"

    def lower_better(actual, target, floor):
        if actual is None or actual <= 0: return None
        return max(0.0, min(1.0, (floor - actual) / (floor - target)))

    def higher_better(actual, target, floor):
        if actual is None: return None
        return max(0.0, min(1.0, (actual - floor) / (target - floor)))

    items = []  # (score, weight)

    # D/E
    de = d.get('debt_to_equity')
    if de is not None:
        s = lower_better(de, 70, 300)
        if s is not None: items.append((s, 1))

    # ROE (yfinance returns as decimal like 0.15 = 15%)
    roe = d.get('return_on_equity')
    if roe is not None:
        roe_pct = roe * 100 if abs(roe) < 5 else roe
        s = higher_better(roe_pct, 15, 0)
        if s is not None:
            w = 2 if sleeve == 'Growth' else 1
            items.append((s, w))

    # Revenue Growth YoY
    rg = d.get('revenue_growth_yoy')
    if rg is not None:
        rg_pct = rg * 100 if abs(rg) < 5 else rg
        s = higher_better(rg_pct, 10, -20)
        if s is not None: items.append((s, 1))

    # Forward P/E
    fpe = d.get('forward_pe')
    if fpe is not None and fpe > 0:
        s = lower_better(fpe, 20, 60)
        if s is not None: items.append((s, 1))

    # Profit Margin
    pm = d.get('profit_margin')
    if pm is not None:
        pm_pct = pm * 100 if abs(pm) < 5 else pm
        s = higher_better(pm_pct, 20, 0)
        if s is not None: items.append((s, 1))

    # Growth: PEG
    if sleeve == 'Growth':
        peg = d.get('peg_ratio')
        if peg is not None and peg > 0:
            s = lower_better(peg, 1.0, 3.0)
            if s is not None: items.append((s, 2))

    # Dividend metrics (simplified - full dividend data often needs additional research)
    if sleeve == 'Dividend':
        pr = d.get('payout_ratio')
        if pr is not None:
            pr_pct = pr * 100 if pr < 5 else pr
            s = lower_better(pr_pct, 40, 100)
            if s is not None: items.append((s, 1))

    if not items:
        return 3, "Insufficient data"

    weighted = sum(s * w for s, w in items)
    max_w = sum(w for _, w in items)
    score = round(weighted / max_w * 10)
    return score, f"Calculated from {len(items)} available metrics"


def determine_sleeve(ticker, d):
    with open('/home/user/Stock-Screener/data/portfolios.json') as f:
        p = json.load(f)
    if ticker in p.get('dividend', []): return 'Dividend'
    if ticker in p.get('growth', []): return 'Growth'

    dy = d.get('dividend_yield') or 0
    if dy > 0.02:
        return 'Dividend'
    rg = d.get('revenue_growth_yoy') or 0
    if rg > 0.15:
        return 'Growth'
    return 'Growth'


def main(tickers):
    results = {}
    for t in tickers:
        d = get_full_data(t)
        sleeve = determine_sleeve(t, d)
        infra_score, infra_note = calc_infrastructure(d, sleeve)
        results[t] = {
            'data': d,
            'sleeve': sleeve,
            'infra_score': infra_score,
            'infra_note': infra_note,
        }
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main(sys.argv[1:])
