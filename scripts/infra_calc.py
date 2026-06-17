"""Pre-compute infrastructure scores and yfinance data for a list of tickers."""
import sys, json, csv, os
sys.path.insert(0, '/home/user/Stock-Screener')
from data.fetcher import fetch_stock_data

def calc_infrastructure(metrics, sleeve):
    """Calculate infrastructure score mechanically per SCREENING.md."""
    def metric_score_lower(actual, target, floor):
        if actual is None: return None
        return max(0.0, min(1.0, (floor - actual) / (floor - target)))
    
    def metric_score_higher(actual, target, floor):
        if actual is None: return None
        return max(0.0, min(1.0, (actual - floor) / (target - floor)))
    
    stock_price = metrics.get('price') or 0
    avg_vol = metrics.get('avg_volume') or 0
    if stock_price * avg_vol < 1_000_000:
        return 0, "LIQUIDITY FLOOR: avg_daily_volume × stock_price < $1M"
    
    scores = []
    weights = []
    
    # Core metrics
    de = metrics.get('debt_to_equity')
    if de is not None:
        s = metric_score_lower(de, 70, 300)
        if s is not None: scores.append(s); weights.append(1)
    
    roe = metrics.get('return_on_equity')
    if roe is not None:
        roe_pct = roe * 100 if abs(roe) < 5 else roe  # handle both decimal and pct
        s = metric_score_higher(roe_pct, 15, 0)
        if s is not None:
            w = 2 if sleeve == 'Growth' else 1
            scores.append(s); weights.append(w)
    
    rev_yoy = metrics.get('revenue_growth')
    if rev_yoy is not None:
        rev_pct = rev_yoy * 100 if abs(rev_yoy) < 5 else rev_yoy
        s = metric_score_higher(rev_pct, 10, -20)
        if s is not None: scores.append(s); weights.append(1)
    
    fwd_pe = metrics.get('forward_pe')
    if fwd_pe is not None and fwd_pe > 0:
        s = metric_score_lower(fwd_pe, 20, 60)
        if s is not None: scores.append(s); weights.append(1)
    
    pm = metrics.get('profit_margin')
    if pm is not None:
        pm_pct = pm * 100 if abs(pm) < 5 else pm
        s = metric_score_higher(pm_pct, 20, 0)
        if s is not None: scores.append(s); weights.append(1)
    
    if not scores:
        return 3, "Insufficient data for mechanical calculation"
    
    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    max_sum = sum(weights)
    infra_score = round(weighted_sum / max_sum * 10)
    return infra_score, f"Calculated from {len(scores)} metrics"

def determine_sleeve(ticker, data):
    with open('/home/user/Stock-Screener/data/portfolios.json') as f:
        portfolios = json.load(f)
    if ticker in portfolios.get('dividend', []): return 'Dividend'
    if ticker in portfolios.get('growth', []): return 'Growth'
    div_yield = data.get('dividend_yield', 0) or 0
    if div_yield > 0.02:
        return 'Dividend'
    rev_growth = data.get('revenue_growth', 0) or 0
    if rev_growth > 0.15:
        return 'Growth'
    return 'Growth'

def main(tickers):
    results = {}
    for ticker in tickers:
        try:
            data_list = fetch_stock_data([ticker])
            d = data_list[0] if data_list else {}
        except:
            d = {}
        
        sleeve = determine_sleeve(ticker, d)
        infra_score, infra_note = calc_infrastructure(d, sleeve)
        
        results[ticker] = {
            'yfinance': d,
            'sleeve': sleeve,
            'infrastructure_score': infra_score,
            'infrastructure_note': infra_note,
            'stock_price': d.get('price'),
            'name': d.get('name', ticker),
            'sector': d.get('sector', ''),
            'industry': d.get('industry', ''),
        }
    
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    tickers = sys.argv[1:]
    main(tickers)
