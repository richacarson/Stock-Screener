"""Generate a report JSON file from scored parameters."""
import json, sys, os, csv
sys.path.insert(0, '/home/user/Stock-Screener')
import yfinance as yf

def get_inspire(ticker):
    with open('/home/user/Stock-Screener/data/inspire_insight_scores.csv', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['ticker'] == ticker:
                score = r.get('score', '0').strip()
                try:
                    score = int(score)
                except:
                    score = 0
                neg = [x.strip() for x in r.get('negative_attributions', '').split('|') if x.strip()]
                pos = [x.strip() for x in r.get('positive_attributions', '').split('|') if x.strip()]
                return score, neg, pos
    return 0, [], []

def get_sleeve(ticker):
    with open('/home/user/Stock-Screener/data/portfolios.json') as f:
        p = json.load(f)
    if ticker in p.get('dividend', []): return 'Dividend'
    if ticker in p.get('growth', []): return 'Growth'
    return None

def calc_infra(metrics, sleeve):
    price = metrics.get('stock_price') or 0
    vol = metrics.get('avg_daily_volume') or 0
    if price * vol < 1_000_000:
        return 0

    def lower(actual, target, floor):
        if actual is None or actual <= 0: return None
        return max(0.0, min(1.0, (floor - actual) / (floor - target)))
    def higher(actual, target, floor):
        if actual is None: return None
        return max(0.0, min(1.0, (actual - floor) / (target - floor)))

    items = []
    de = metrics.get('debt_to_equity')
    if de is not None:
        s = lower(de, 70, 300)
        if s is not None: items.append((s, 1))

    roe = metrics.get('return_on_equity')
    if roe is not None:
        s = higher(roe, 15, 0)
        if s is not None: items.append((s, 2 if sleeve == 'Growth' else 1))

    rg = metrics.get('revenue_growth_yoy')
    if rg is not None:
        s = higher(rg, 10, -20)
        if s is not None: items.append((s, 1))

    fpe = metrics.get('forward_pe')
    if fpe is not None and fpe > 0:
        s = lower(fpe, 20, 60)
        if s is not None: items.append((s, 1))

    pm = metrics.get('profit_margin')
    if pm is not None:
        s = higher(pm, 20, 0)
        if s is not None: items.append((s, 1))

    if sleeve == 'Growth':
        peg = metrics.get('peg_ratio')
        if peg is not None and peg > 0:
            s = lower(peg, 1.0, 3.0)
            if s is not None: items.append((s, 2))

    if sleeve == 'Dividend':
        pr = metrics.get('payout_ratio')
        if pr is not None and pr > 0:
            s = lower(pr, 40, 100)
            if s is not None: items.append((s, 1))

    if not items: return 3
    weighted = sum(s * w for s, w in items)
    max_w = sum(w for _, w in items)
    return round(weighted / max_w * 10)

def get_yf_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="3mo")
        price = round(float(hist["Close"].iloc[-1]), 2) if not hist.empty else None
        avg_vol = round(float(hist["Volume"].mean())) if not hist.empty else None
        roe_raw = info.get('returnOnEquity')
        roe_pct = round(roe_raw * 100, 1) if roe_raw else None
        pm_raw = info.get('profitMargins')
        pm_pct = round(pm_raw * 100, 1) if pm_raw else None
        rg_raw = info.get('revenueGrowth')
        rg_pct = round(rg_raw * 100, 1) if rg_raw else None
        eg_raw = info.get('earningsGrowth')
        eg_pct = round(eg_raw * 100, 1) if eg_raw else None
        dy_raw = info.get('dividendYield')
        dy_pct = round(dy_raw * 100, 2) if dy_raw else None
        pr_raw = info.get('payoutRatio')
        pr_pct = round(pr_raw * 100, 1) if pr_raw else None
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
            'pe_ratio': round(info.get('trailingPE'), 1) if info.get('trailingPE') else None,
            'forward_pe': round(info.get('forwardPE'), 1) if info.get('forwardPE') else None,
            'peg_ratio': round(info.get('pegRatio'), 2) if info.get('pegRatio') else None,
            'debt_to_equity': round(info.get('debtToEquity'), 1) if info.get('debtToEquity') is not None else None,
            'return_on_equity': roe_pct,
            'profit_margin': pm_pct,
            'revenue_growth_yoy': rg_pct,
            'earnings_growth_yoy': eg_pct,
            'avg_daily_volume': avg_vol,
            'dividend_yield': dy_pct,
            'payout_ratio': pr_pct,
            'market_cap': info.get('marketCap'),
        }
    except Exception as e:
        return {'name': ticker, 'error': str(e)}

def build_report(ticker, scores, analyses, yf_data=None):
    if yf_data is None:
        yf_data = get_yf_data(ticker)

    inspire_score, neg_attr, pos_attr = get_inspire(ticker)
    forced_sleeve = get_sleeve(ticker)

    dy = yf_data.get('dividend_yield') or 0
    rg = yf_data.get('revenue_growth_yoy') or 0
    if forced_sleeve:
        sleeve = forced_sleeve
    elif dy > 2 and scores.get('div_years', 0) >= 5:
        sleeve = 'Dividend'
    else:
        sleeve = 'Growth'

    metrics = {
        'stock_price': yf_data.get('stock_price'),
        'pe_ratio': yf_data.get('pe_ratio'),
        'forward_pe': yf_data.get('forward_pe'),
        'peg_ratio': yf_data.get('peg_ratio'),
        'debt_to_equity': yf_data.get('debt_to_equity'),
        'return_on_equity': yf_data.get('return_on_equity'),
        'profit_margin': yf_data.get('profit_margin'),
        'revenue_growth_yoy': yf_data.get('revenue_growth_yoy'),
        'avg_daily_volume': yf_data.get('avg_daily_volume'),
    }
    # For infra calc, need raw decimals
    infra_metrics = {
        'stock_price': yf_data.get('stock_price'),
        'avg_daily_volume': yf_data.get('avg_daily_volume'),
        'debt_to_equity': yf_data.get('debt_to_equity'),
        'return_on_equity': yf_data.get('return_on_equity'),
        'profit_margin': yf_data.get('profit_margin'),
        'revenue_growth_yoy': yf_data.get('revenue_growth_yoy'),
        'forward_pe': yf_data.get('forward_pe'),
        'peg_ratio': yf_data.get('peg_ratio'),
        'payout_ratio': yf_data.get('payout_ratio'),
    }
    infra_score = calc_infra(infra_metrics, sleeve)

    innov = scores['innovation']
    inspir = scores['inspiration']
    ai_res = scores['ai_resilience']
    ig = scores['infinite_game']

    overall = round(
        (innov + inspir + infra_score) / 3 / 10 * 50
        + ai_res / 10 * 25
        + ig / 10 * 25
    )

    def label10(s): return "STRONG" if s >= 7 else ("DEVELOPING" if s >= 4 else "WEAK")
    def ai_label(s): return "LOW RISK" if s >= 7 else ("MODERATE" if s >= 4 else "HIGH RISK")
    def ig_mindset(s): return "INFINITE" if s >= 8 else ("MIXED" if s >= 5 else "FINITE")
    def faith_label(s): return "ALIGNED" if s > 25 else ("MIXED" if s >= -25 else "MISALIGNED")
    def rec(s): return "BUY" if s >= 80 else ("HOLD" if s >= 60 else ("WATCH" if s >= 40 else "SELL"))

    # Infinite game display scores
    jc_pts = scores.get('jc_pts', 0)
    cour_pts = scores.get('cour_pts', 0)
    trust_pts = scores.get('trust_pts', 0)
    flex_pts = scores.get('flex_pts', 0)
    rival_pts = scores.get('rival_pts', 0)
    jc_display = {0:1, 1:4, 2:7, 3:10}.get(jc_pts, 1)
    cour_display = {0:2, 1:6, 2:10}.get(cour_pts, 2)
    trust_display = {0:2, 1:6, 2:10}.get(trust_pts, 2)
    flex_display = {0:2, 1:6, 2:10}.get(flex_pts, 2)
    rival_display = {0:3, 1:10}.get(rival_pts, 3)

    # Build dividend metrics if applicable
    infra_metrics_json = {
        'stock_price': yf_data.get('stock_price'),
        'pe_ratio': yf_data.get('pe_ratio'),
        'forward_pe': yf_data.get('forward_pe'),
        'peg_ratio': yf_data.get('peg_ratio'),
        'debt_to_equity': yf_data.get('debt_to_equity'),
        'return_on_equity': yf_data.get('return_on_equity'),
        'profit_margin': yf_data.get('profit_margin'),
        'eps_growth_yoy': yf_data.get('earnings_growth_yoy'),
        'eps_growth_5yr_cagr': None,
        'revenue_growth_yoy': yf_data.get('revenue_growth_yoy'),
        'revenue_growth_5yr_cagr': None,
        'avg_daily_volume': yf_data.get('avg_daily_volume'),
    }
    if sleeve == 'Dividend':
        infra_metrics_json['dividend'] = {
            'yield': yf_data.get('dividend_yield'),
            'payout_ratio': yf_data.get('payout_ratio'),
            'consecutive_years_paid': scores.get('div_years', None),
            'consecutive_years_growth': scores.get('div_growth_years', None),
            'dividend_growth_5yr_cagr': scores.get('div_growth_cagr', None),
        }

    report = {
        'ticker': ticker,
        'name': yf_data.get('name', ticker),
        'sleeve': sleeve,
        'recommendation': rec(overall),
        'screen_date': '2026-06-01',
        'overall_score': overall,
        'profile': {
            'sector': yf_data.get('sector', 'Unknown'),
            'industry': yf_data.get('industry', 'Unknown'),
            'exchange': yf_data.get('exchange', ''),
            'country': yf_data.get('country', 'United States'),
            'website': yf_data.get('website', ''),
            'employees': yf_data.get('employees'),
            'description': yf_data.get('description', ''),
        },
        'excellence_evaluation': {
            'innovation': {
                'score': innov,
                'label': label10(innov),
                'analysis': analyses.get('innovation', ''),
            },
            'inspiration': {
                'score': inspir,
                'label': label10(inspir),
                'analysis': analyses.get('inspiration', ''),
            },
            'infrastructure': {
                'score': infra_score,
                'label': label10(infra_score),
                'analysis': analyses.get('infrastructure', ''),
                'metrics': infra_metrics_json,
            },
        },
        'ai_resilience': {
            'score': ai_res,
            'label': ai_label(ai_res),
            'analysis': analyses.get('ai_resilience', ''),
        },
        'infinite_game': {
            'mindset': ig_mindset(ig),
            'overall': ig,
            'summary': analyses.get('ig_summary', ''),
            'just_cause': {'score': jc_display, 'analysis': analyses.get('just_cause', '')},
            'trusting_teams': {'score': trust_display, 'analysis': analyses.get('trusting_teams', '')},
            'worthy_rivals': {'score': rival_display, 'analysis': analyses.get('worthy_rivals', '')},
            'existential_flexibility': {'score': flex_display, 'analysis': analyses.get('existential_flexibility', '')},
            'courage_to_lead': {'score': cour_display, 'analysis': analyses.get('courage_to_lead', '')},
        },
        'faith_alignment': {
            'inspire_impact_score': inspire_score,
            'label': faith_label(inspire_score),
            'negative_attributions': neg_attr,
            'positive_attributions': pos_attr,
            'source': 'Inspire Insight',
        },
        'investment_thesis': analyses.get('thesis', ''),
        'thesis_continued': analyses.get('thesis_bear', ''),
        'key_catalysts': analyses.get('catalysts', []),
        'key_risks': analyses.get('risks', []),
        'sources': analyses.get('sources', []),
    }

    path = f'/home/user/Stock-Screener/reports/{ticker}.json'
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Wrote {path} — overall={overall} rec={rec(overall)} sleeve={sleeve} infra={infra_score}")
    return report

if __name__ == '__main__':
    ticker = sys.argv[1]
    print(json.dumps(get_yf_data(ticker), indent=2))
