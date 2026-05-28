#!/usr/bin/env python3
"""Generate an IOWN report JSON from scoring inputs + yfinance data."""
import json
import sys
import csv
import os
from datetime import date

def fetch_yfinance(ticker):
    try:
        sys.path.insert(0, '/home/user/Stock-Screener')
        from data.fetcher import fetch_stock_data
        data = fetch_stock_data([ticker])
        return data[0] if data else {}
    except Exception as e:
        print(f"yfinance error for {ticker}: {e}", file=sys.stderr)
        return {}

def get_inspire(ticker):
    csv_path = '/home/user/Stock-Screener/data/inspire_insight_scores.csv'
    with open(csv_path, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if row['ticker'] == ticker:
                score = row.get('score', '0')
                try:
                    score = int(score)
                except:
                    score = 0
                neg = [x.strip() for x in row.get('negative_attributions', '').split('|') if x.strip()]
                pos = [x.strip() for x in row.get('positive_attributions', '').split('|') if x.strip()]
                if score > 25:
                    label = "ALIGNED"
                elif score < -25:
                    label = "MISALIGNED"
                else:
                    label = "MIXED"
                return {"inspire_impact_score": score, "label": label, "negative_attributions": neg, "positive_attributions": pos, "source": "Inspire Insight"}
    return {"inspire_impact_score": 0, "label": "MIXED", "negative_attributions": [], "positive_attributions": [], "source": "Inspire Insight"}

def get_portfolio_sleeve(ticker):
    pf_path = '/home/user/Stock-Screener/data/portfolios.json'
    with open(pf_path) as f:
        pf = json.load(f)
    if ticker in pf.get('dividend', []):
        return "Dividend"
    if ticker in pf.get('growth', []):
        return "Growth"
    return None

def calc_infrastructure(metrics, sleeve):
    """Calculate infrastructure score mechanically per SCREENING.md."""
    def score_lower(actual, target, floor):
        if actual is None: return None
        return max(0, min(1, (floor - actual) / (floor - target)))

    def score_higher(actual, target, floor):
        if actual is None: return None
        return max(0, min(1, (actual - floor) / (target - floor)))

    de = metrics.get('debt_to_equity')
    roe = metrics.get('return_on_equity')
    rev_yoy = metrics.get('revenue_growth_yoy')
    rev_5yr = metrics.get('revenue_growth_5yr_cagr')
    fwd_pe = metrics.get('forward_pe')
    pm = metrics.get('profit_margin')
    peg = metrics.get('peg_ratio')

    core = [
        (score_lower(de, 70, 300), 1),
        (score_higher(roe, 15, 0), 2 if sleeve == "Growth" else 1),
        (score_higher(rev_yoy, 10, -20), 1),
        (score_higher(rev_5yr, 10, -5), 2 if sleeve == "Growth" else 1),
        (score_lower(fwd_pe, 20, 60), 1),
        (score_higher(pm, 20, 0), 1),
    ]

    if sleeve == "Dividend":
        div = metrics.get('dividend', {}) or {}
        core.extend([
            (score_lower(div.get('payout_ratio'), 40, 100), 1),
            (score_higher(div.get('consecutive_years_paid'), 10, 0), 2),
            (score_higher(div.get('consecutive_years_growth'), 10, 0), 1),
            (score_higher(div.get('dividend_growth_5yr_cagr'), 6, 0), 2),
        ])
    else:
        core.append((score_lower(peg, 1.0, 3.0), 2))

    weighted_sum = 0
    max_sum = 0
    for s, w in core:
        if s is not None:
            weighted_sum += s * w
            max_sum += w

    if max_sum == 0:
        return 0

    raw = weighted_sum / max_sum * 10
    return round(raw)

def infra_label(score):
    if score >= 7: return "STRONG"
    if score >= 4: return "DEVELOPING"
    return "WEAK"

def sub_label(score, dimension="default"):
    if dimension == "ai":
        if score >= 8: return "LOW RISK"
        if score >= 5: return "MODERATE"
        return "HIGH RISK"
    if score >= 7: return "STRONG"
    if score >= 4: return "DEVELOPING"
    return "WEAK"

def ig_mindset(overall):
    if overall >= 8: return "INFINITE"
    if overall >= 5: return "MIXED"
    return "FINITE"

def recommendation(score):
    if score >= 80: return "BUY"
    if score >= 60: return "HOLD"
    if score >= 40: return "WATCH"
    return "SELL"

def generate_report(params):
    ticker = params['ticker']
    yf = fetch_yfinance(ticker)
    inspire = get_inspire(ticker)
    forced_sleeve = get_portfolio_sleeve(ticker)

    stock_price = yf.get('price') or params.get('stock_price')
    avg_vol = yf.get('avg_volume') or params.get('avg_daily_volume', 0)

    metrics = {
        "stock_price": stock_price,
        "pe_ratio": yf.get('pe_ratio') or params.get('pe_ratio'),
        "forward_pe": yf.get('forward_pe') or params.get('forward_pe'),
        "peg_ratio": params.get('peg_ratio'),
        "debt_to_equity": yf.get('debt_to_equity') or params.get('debt_to_equity'),
        "return_on_equity": (yf.get('return_on_equity', 0) or 0) * 100 if yf.get('return_on_equity') is not None and yf.get('return_on_equity') < 5 else yf.get('return_on_equity') or params.get('return_on_equity'),
        "profit_margin": (yf.get('profit_margin', 0) or 0) * 100 if yf.get('profit_margin') is not None and abs(yf.get('profit_margin', 0)) < 5 else yf.get('profit_margin') or params.get('profit_margin'),
        "eps_growth_yoy": params.get('eps_growth_yoy'),
        "eps_growth_5yr_cagr": params.get('eps_growth_5yr_cagr'),
        "revenue_growth_yoy": (yf.get('revenue_growth', 0) or 0) * 100 if yf.get('revenue_growth') is not None and abs(yf.get('revenue_growth', 0)) < 5 else yf.get('revenue_growth') or params.get('revenue_growth_yoy'),
        "revenue_growth_5yr_cagr": params.get('revenue_growth_5yr_cagr'),
        "avg_daily_volume": avg_vol,
        "dividend": params.get('dividend'),
    }

    if forced_sleeve:
        sleeve = forced_sleeve
    elif params.get('sleeve'):
        sleeve = params['sleeve']
    else:
        div = metrics.get('dividend')
        if div and div.get('consecutive_years_paid', 0) >= 5 and div.get('yield', 0) > 2:
            sleeve = "Dividend"
        else:
            sleeve = "Growth"

    liquidity = (stock_price or 0) * (avg_vol or 0)
    if liquidity < 1_000_000:
        infra_score = 0
    else:
        infra_score = calc_infrastructure(metrics, sleeve)

    innovation = params['innovation']
    inspiration = params['inspiration']
    ai_resilience = params['ai_resilience']
    ig_overall = params['infinite_game_overall']

    excellence_avg = (innovation + inspiration + infra_score) / 3
    overall_score = round(excellence_avg / 10 * 50 + ai_resilience / 10 * 25 + ig_overall / 10 * 25)
    rec = recommendation(overall_score)

    report = {
        "ticker": ticker,
        "name": params['name'],
        "sleeve": sleeve,
        "recommendation": rec,
        "screen_date": str(date.today()),
        "overall_score": overall_score,
        "profile": params['profile'],
        "excellence_evaluation": {
            "innovation": {
                "score": innovation,
                "label": sub_label(innovation),
                "analysis": params['innovation_analysis']
            },
            "inspiration": {
                "score": inspiration,
                "label": sub_label(inspiration),
                "analysis": params['inspiration_analysis']
            },
            "infrastructure": {
                "score": infra_score,
                "label": infra_label(infra_score),
                "analysis": params['infrastructure_analysis'],
                "metrics": metrics
            }
        },
        "ai_resilience": {
            "score": ai_resilience,
            "label": sub_label(ai_resilience, "ai"),
            "analysis": params['ai_analysis']
        },
        "infinite_game": {
            "mindset": ig_mindset(ig_overall),
            "overall": ig_overall,
            "summary": params['ig_summary'],
            "just_cause": {"score": params['ig_just_cause_display'], "analysis": params['ig_just_cause_analysis']},
            "trusting_teams": {"score": params['ig_trusting_display'], "analysis": params['ig_trusting_analysis']},
            "worthy_rivals": {"score": params['ig_rivals_display'], "analysis": params['ig_rivals_analysis']},
            "existential_flexibility": {"score": params['ig_flex_display'], "analysis": params['ig_flex_analysis']},
            "courage_to_lead": {"score": params['ig_courage_display'], "analysis": params['ig_courage_analysis']}
        },
        "faith_alignment": inspire,
        "investment_thesis": params['thesis_bull'],
        "thesis_continued": params['thesis_bear'],
        "key_catalysts": params['catalysts'],
        "key_risks": params['risks'],
        "sources": params['sources']
    }

    outpath = f'/home/user/Stock-Screener/reports/{ticker}.json'
    with open(outpath, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Written {outpath} — Score: {overall_score}, Rec: {rec}, Sleeve: {sleeve}")
    return report

if __name__ == '__main__':
    params_json = sys.argv[1]
    params = json.loads(params_json)
    generate_report(params)
