#!/usr/bin/env python3
"""Refresh stock reports with fresh yfinance data and recalculated scores."""

import json
import os
import sys
import yfinance as yf
from datetime import datetime

TODAY = "2026-06-10"
REPORTS_DIR = "/home/user/Stock-Screener/reports"

# Portfolio holdings for sleeve forcing
with open("/home/user/Stock-Screener/data/portfolios.json") as f:
    PORTFOLIOS = json.load(f)
DIVIDEND_HOLDINGS = set(PORTFOLIOS["dividend"])
GROWTH_HOLDINGS = set(PORTFOLIOS["growth"])


def fetch_metrics(ticker: str) -> dict | None:
    """Fetch comprehensive metrics from yfinance."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        hist = t.history(period="3mo")
        if hist.empty:
            return None

        price = round(float(hist["Close"].iloc[-1]), 2)
        avg_vol = round(float(hist["Volume"].mean()))

        # Get dividend info
        div_info = None
        div_yield = info.get("dividendYield")
        if div_yield and div_yield > 0:
            div_info = {
                "yield": round(div_yield * 100, 2) if div_yield < 1 else round(div_yield, 2),
                "payout_ratio": round(info.get("payoutRatio", 0) * 100, 1) if info.get("payoutRatio") else None,
                "consecutive_years_paid": None,
                "consecutive_years_growth": None,
                "dividend_growth_5yr_cagr": None,
            }

        return {
            "stock_price": price,
            "pe_ratio": round(info.get("trailingPE", 0), 1) if info.get("trailingPE") else None,
            "forward_pe": round(info.get("forwardPE", 0), 1) if info.get("forwardPE") else None,
            "peg_ratio": round(info.get("pegRatio", 0), 2) if info.get("pegRatio") else None,
            "debt_to_equity": round(info.get("debtToEquity", 0), 1) if info.get("debtToEquity") else None,
            "return_on_equity": round(info.get("returnOnEquity", 0) * 100, 1) if info.get("returnOnEquity") else None,
            "profit_margin": round(info.get("profitMargins", 0) * 100, 1) if info.get("profitMargins") else None,
            "eps_growth_yoy": round(info.get("earningsGrowth", 0) * 100, 1) if info.get("earningsGrowth") else None,
            "eps_growth_5yr_cagr": None,
            "revenue_growth_yoy": round(info.get("revenueGrowth", 0) * 100, 1) if info.get("revenueGrowth") else None,
            "revenue_growth_5yr_cagr": None,
            "avg_daily_volume": avg_vol,
            "dividend": div_info,
            # Extra info for profile
            "_name": info.get("shortName", ticker),
            "_sector": info.get("sector", "Unknown"),
            "_industry": info.get("industry", "Unknown"),
            "_exchange": info.get("exchange", ""),
            "_country": info.get("country", ""),
            "_website": info.get("website", ""),
            "_employees": info.get("fullTimeEmployees"),
            "_description": info.get("longBusinessSummary", ""),
        }
    except Exception as e:
        print(f"  Error fetching {ticker}: {e}")
        return None


def metric_score_lower(actual, target, floor):
    """Lower is better: D/E, Forward P/E, Payout Ratio, PEG."""
    if actual is None:
        return None
    return max(0.0, min(1.0, (floor - actual) / (floor - target)))


def metric_score_higher(actual, target, floor):
    """Higher is better: ROE, Rev Growth, Profit Margin, etc."""
    if actual is None:
        return None
    return max(0.0, min(1.0, (actual - floor) / (target - floor)))


def calc_infrastructure(metrics: dict, is_dividend: bool) -> int:
    """Calculate infrastructure score mechanically."""
    # Liquidity floor
    price = metrics.get("stock_price", 0) or 0
    vol = metrics.get("avg_daily_volume", 0) or 0
    if price * vol < 1_000_000:
        return 0

    scores = []  # (metric_score, weight)

    # Core metrics
    de = metrics.get("debt_to_equity")
    if de is not None:
        scores.append((metric_score_lower(de, 70, 300), 1))

    roe = metrics.get("return_on_equity")
    if roe is not None:
        w = 2 if not is_dividend else 1
        scores.append((metric_score_higher(roe, 15, 0), w))

    rev_yoy = metrics.get("revenue_growth_yoy")
    if rev_yoy is not None:
        scores.append((metric_score_higher(rev_yoy, 10, -20), 1))

    rev_5yr = metrics.get("revenue_growth_5yr_cagr")
    if rev_5yr is not None:
        w = 2 if not is_dividend else 1
        scores.append((metric_score_higher(rev_5yr, 10, -5), w))

    fwd_pe = metrics.get("forward_pe")
    if fwd_pe is not None:
        scores.append((metric_score_lower(fwd_pe, 20, 60), 1))

    margin = metrics.get("profit_margin")
    if margin is not None:
        scores.append((metric_score_higher(margin, 20, 0), 1))

    if is_dividend and metrics.get("dividend"):
        div = metrics["dividend"]
        pr = div.get("payout_ratio")
        if pr is not None:
            scores.append((metric_score_lower(pr, 40, 100), 1))

        yrs_paid = div.get("consecutive_years_paid")
        if yrs_paid is not None:
            scores.append((metric_score_higher(yrs_paid, 10, 0), 2))

        yrs_growth = div.get("consecutive_years_growth")
        if yrs_growth is not None:
            scores.append((metric_score_higher(yrs_growth, 10, 0), 1))

        div_growth = div.get("dividend_growth_5yr_cagr")
        if div_growth is not None:
            scores.append((metric_score_higher(div_growth, 6, 0), 2))
    elif not is_dividend:
        peg = metrics.get("peg_ratio")
        if peg is not None:
            scores.append((metric_score_lower(peg, 1.0, 3.0), 2))

    # Filter out None scores
    valid = [(s, w) for s, w in scores if s is not None]
    if not valid:
        return 0

    weighted_sum = sum(s * w for s, w in valid)
    max_weight = sum(w for _, w in valid)
    return round(weighted_sum / max_weight * 10)


def calc_overall(report: dict) -> int:
    """Calculate overall score from sub-scores."""
    innov = report["excellence_evaluation"]["innovation"]["score"]
    inspir = report["excellence_evaluation"]["inspiration"]["score"]
    infra = report["excellence_evaluation"]["infrastructure"]["score"]
    ai = report["ai_resilience"]["score"]
    ig = report["infinite_game"]["overall"]

    overall = (innov + inspir + infra) / 3 / 10 * 50 + ai / 10 * 25 + ig / 10 * 25
    return round(overall)


def get_recommendation(score: int) -> str:
    if score >= 80:
        return "BUY"
    elif score >= 60:
        return "HOLD"
    elif score >= 40:
        return "WATCH"
    else:
        return "SELL"


def get_label(score: int, category: str) -> str:
    if category == "infra":
        if score >= 7: return "STRONG"
        elif score >= 4: return "DEVELOPING"
        else: return "WEAK"
    elif category == "ai":
        if score >= 8: return "LOW RISK"
        elif score >= 5: return "MODERATE"
        else: return "HIGH RISK"
    return ""


def determine_sleeve(ticker: str, metrics: dict, existing_sleeve: str) -> str:
    """Determine sleeve assignment."""
    if ticker in DIVIDEND_HOLDINGS:
        return "Dividend"
    if ticker in GROWTH_HOLDINGS:
        return "Growth"
    # Auto-classify
    div = metrics.get("dividend")
    if div:
        yrs = div.get("consecutive_years_paid")
        dy = div.get("yield", 0) or 0
        if yrs and yrs >= 5 and dy > 2:
            return "Dividend"
    return "Growth"


def refresh_report(ticker: str, fresh: dict) -> bool:
    """Refresh a single report with fresh data."""
    path = os.path.join(REPORTS_DIR, f"{ticker}.json")
    with open(path) as f:
        report = json.load(f)

    old_metrics = report["excellence_evaluation"]["infrastructure"].get("metrics", {})

    # Preserve fields that yfinance doesn't provide but existing report has
    new_metrics = {
        "stock_price": fresh["stock_price"],
        "pe_ratio": fresh["pe_ratio"],
        "forward_pe": fresh["forward_pe"],
        "peg_ratio": fresh["peg_ratio"],
        "debt_to_equity": fresh["debt_to_equity"],
        "return_on_equity": fresh["return_on_equity"],
        "profit_margin": fresh["profit_margin"],
        "eps_growth_yoy": fresh["eps_growth_yoy"],
        "eps_growth_5yr_cagr": fresh.get("eps_growth_5yr_cagr") or old_metrics.get("eps_growth_5yr_cagr"),
        "revenue_growth_yoy": fresh["revenue_growth_yoy"],
        "revenue_growth_5yr_cagr": fresh.get("revenue_growth_5yr_cagr") or old_metrics.get("revenue_growth_5yr_cagr"),
        "avg_daily_volume": fresh["avg_daily_volume"],
    }

    # Handle dividend - preserve existing dividend details if fresh doesn't have them
    if fresh["dividend"]:
        old_div = old_metrics.get("dividend", {}) or {}
        new_metrics["dividend"] = {
            "yield": fresh["dividend"]["yield"],
            "payout_ratio": fresh["dividend"]["payout_ratio"] or old_div.get("payout_ratio"),
            "consecutive_years_paid": old_div.get("consecutive_years_paid"),
            "consecutive_years_growth": old_div.get("consecutive_years_growth"),
            "dividend_growth_5yr_cagr": old_div.get("dividend_growth_5yr_cagr"),
        }
    elif old_metrics.get("dividend"):
        new_metrics["dividend"] = old_metrics["dividend"]
    else:
        new_metrics["dividend"] = None

    # Determine sleeve and dividend status
    sleeve = determine_sleeve(ticker, new_metrics, report.get("sleeve", "Growth"))
    is_dividend = sleeve == "Dividend"

    # Calculate new infrastructure score
    new_infra = calc_infrastructure(new_metrics, is_dividend)

    # Update report
    report["screen_date"] = TODAY
    report["sleeve"] = sleeve
    report["excellence_evaluation"]["infrastructure"]["metrics"] = new_metrics
    report["excellence_evaluation"]["infrastructure"]["score"] = new_infra
    report["excellence_evaluation"]["infrastructure"]["label"] = get_label(new_infra, "infra")

    # Update profile if we got better data
    if fresh.get("_name") and fresh["_name"] != ticker:
        report["name"] = fresh["_name"]
    if fresh.get("_sector") and fresh["_sector"] != "Unknown":
        report["profile"]["sector"] = fresh["_sector"]
    if fresh.get("_industry") and fresh["_industry"] != "Unknown":
        report["profile"]["industry"] = fresh["_industry"]
    if fresh.get("_employees"):
        report["profile"]["employees"] = fresh["_employees"]

    # Recalculate overall score
    report["overall_score"] = calc_overall(report)
    report["recommendation"] = get_recommendation(report["overall_score"])

    # Write
    with open(path, "w") as f:
        json.dump(report, f, indent=2)

    return True


def main():
    tickers = sys.argv[1:] if len(sys.argv) > 1 else []
    if not tickers:
        print("Usage: python3 scripts/refresh_reports.py TICKER1 TICKER2 ...")
        sys.exit(1)

    success = 0
    failed = []

    for i, ticker in enumerate(tickers):
        print(f"[{i+1}/{len(tickers)}] Refreshing {ticker}...", end=" ", flush=True)
        fresh = fetch_metrics(ticker)
        if fresh is None:
            print("FAILED (no data)")
            failed.append(ticker)
            continue

        try:
            refresh_report(ticker, fresh)
            report = json.load(open(os.path.join(REPORTS_DIR, f"{ticker}.json")))
            print(f"OK score={report['overall_score']} rec={report['recommendation']} date={report['screen_date']}")
            success += 1
        except Exception as e:
            print(f"FAILED ({e})")
            failed.append(ticker)

    print(f"\nDone: {success} refreshed, {len(failed)} failed")
    if failed:
        print(f"Failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()
