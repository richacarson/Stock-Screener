#!/usr/bin/env python3
"""IOWN Stock Screener — Entry point."""

import json
import os
from datetime import datetime
from pathlib import Path

from data.fetcher import fetch_stock_data
from screener.filters import apply_filters
from screener.rankings import rank_stocks

# Default universe — S&P 500 large-caps + IOWN holdings
DEFAULT_TICKERS = [
    # IOWN Dividend Sleeve
    "ABT", "A", "ADI", "ATO", "ADP", "BKH", "CAT", "CHD", "CL", "FAST",
    "GD", "GPC", "LRCX", "LMT", "MATX", "NEE", "ORI", "PCAR", "QCOM", "DGX",
    "SSNC", "STLD", "SYK", "TEL", "VLO",
    # IOWN Growth Sleeve
    "AMD", "AEM", "ATAT", "CVX", "CWAN", "CNX", "COIN", "EIX", "FINV", "FTNT",
    "GFI", "SUPV", "HRMY", "HUT", "KEYS", "MARA", "NVDA", "NXPI", "OKE", "PDD",
    "HOOD", "SYF", "TSM", "TOL",
    # Additional large-caps for screening
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "JPM", "V", "MA",
    "UNH", "HD", "PG", "JNJ", "XOM", "AVGO", "COST", "ABBV", "WMT", "CRM",
    "MRK", "LLY", "PEP", "KO", "TMO", "ACN", "ORCL", "MCD", "DHR", "CSCO",
]


def run_screener(tickers: list[str] | None = None) -> dict:
    """Run the full screening pipeline."""
    tickers = tickers or DEFAULT_TICKERS
    print(f"[{datetime.now():%H:%M:%S}] Fetching data for {len(tickers)} tickers...")

    # Fetch
    raw_data = fetch_stock_data(tickers)
    print(f"[{datetime.now():%H:%M:%S}] Got data for {len(raw_data)} stocks")

    # Filter
    passed = apply_filters(raw_data)
    print(f"[{datetime.now():%H:%M:%S}] {len(passed)} stocks passed filters")

    # Rank
    ranked = rank_stocks(passed)
    print(f"[{datetime.now():%H:%M:%S}] Ranking complete")

    results = {
        "generated_at": datetime.now().isoformat(),
        "total_screened": len(raw_data),
        "total_passed": len(ranked),
        "stocks": ranked,
    }

    # Save results
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[{datetime.now():%H:%M:%S}] Results saved to output/results.json")

    # Generate HTML report
    generate_html_report(results, output_dir / "index.html")
    print(f"[{datetime.now():%H:%M:%S}] Report saved to output/index.html")

    return results


def generate_html_report(results: dict, output_path: Path) -> None:
    """Generate HTML report from screening results."""
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("report.html")
    html = template.render(
        results=results,
        generated_at=results["generated_at"],
        total_screened=results["total_screened"],
        total_passed=results["total_passed"],
    )
    output_path.write_text(html)


if __name__ == "__main__":
    run_screener()
