#!/usr/bin/env python3
"""IOWN Stock Screener — Generates static site from report JSON files.

Reads pre-generated IOWN analysis reports from reports/*.json,
builds an index page with search, and individual stock report pages.
"""

import json
import re
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup
from screener.docx_export import generate_docx


REPORTS_DIR = Path("reports")
OPPORTUNITIES_DIR = Path("opportunities")
OUTPUT_DIR = Path("output")

_SOURCE_RE = re.compile(r"\[(\d+)\]")


def _sourceref_filter(text: str) -> Markup:
    """Convert [1], [2] etc. in text to superscript source references."""
    if not text:
        return Markup("")
    escaped = Markup.escape(text)
    result = _SOURCE_RE.sub(r'<span class="source-ref">[\1]</span>', str(escaped))
    return Markup(result)


def build_site() -> None:
    """Build the full static site from report JSON files."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    env = Environment(loader=FileSystemLoader("templates"))
    env.filters["sourceref"] = _sourceref_filter

    # Load all reports
    reports = _load_reports()
    print(f"[{datetime.now():%H:%M:%S}] Loaded {len(reports)} stock reports")

    if not reports:
        print("No reports found in reports/. Nothing to build.")
        return

    # Sort by overall score descending
    reports.sort(key=lambda r: r.get("overall_score", 0), reverse=True)

    # Build index page
    _build_index(env, reports)
    print(f"[{datetime.now():%H:%M:%S}] Built index.html")

    # Build individual stock pages
    for report in reports:
        _build_stock_page(env, report)
    print(f"[{datetime.now():%H:%M:%S}] Built {len(reports)} stock pages")

    # Generate Word docs
    docx_out = OUTPUT_DIR / "docx"
    docx_out.mkdir(exist_ok=True)
    for report in reports:
        ticker = report["ticker"]
        docx_bytes = generate_docx(report)
        (docx_out / f"{ticker}_IOWN_Report.docx").write_bytes(docx_bytes)
    print(f"[{datetime.now():%H:%M:%S}] Built {len(reports)} Word docs")

    # Copy reports as JSON for frontend use
    reports_out = OUTPUT_DIR / "reports"
    reports_out.mkdir(exist_ok=True)
    for report in reports:
        ticker = report["ticker"]
        with open(reports_out / f"{ticker}.json", "w") as f:
            json.dump(report, f, indent=2, default=str)

    # Build manifest for search
    manifest = [
        {
            "ticker": r["ticker"],
            "name": r["name"],
            "sleeve": r.get("sleeve", ""),
            "recommendation": r.get("recommendation", ""),
            "overall_score": r.get("overall_score", 0),
            "screen_date": r.get("screen_date", ""),
        }
        for r in reports
    ]
    with open(OUTPUT_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[{datetime.now():%H:%M:%S}] Build complete — {len(reports)} reports")


def _load_reports() -> list[dict]:
    """Load all report JSON files from reports/."""
    reports = []
    for path in sorted(REPORTS_DIR.glob("*.json")):
        try:
            with open(path) as f:
                data = json.load(f)
            _normalize_report(data)
            reports.append(data)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  Warning: Failed to load {path.name}: {e}")
    return reports


def _normalize_report(data: dict) -> None:
    """Normalize old report schemas to the current 3-dimension format."""
    # Promote ai_resilience from risk_moat_erosion if needed
    if "ai_resilience" not in data and "risk_moat_erosion" in data:
        rme = data["risk_moat_erosion"]
        if "ai_resilience" in rme:
            data["ai_resilience"] = rme["ai_resilience"]

    # Ensure ai_resilience exists with fallback
    if "ai_resilience" not in data:
        data["ai_resilience"] = {"score": 0, "label": "N/A", "analysis": ""}


_OPP_SUPPORT_FILES = {
    "manifest.json", "ledger.json", "signals.json", "stalking.json",
    "committee_lookup.json", "fund_cik_lookup.json", "team_feedback.json",
}


def _load_opportunities() -> list[dict]:
    """Load active opportunity JSON files."""
    opportunities = []
    if not OPPORTUNITIES_DIR.exists():
        return opportunities
    for path in sorted(OPPORTUNITIES_DIR.glob("*.json")):
        if path.name in _OPP_SUPPORT_FILES:
            continue
        try:
            with open(path) as f:
                data = json.load(f)
            if isinstance(data, dict) and data.get("status") == "active":
                opportunities.append(data)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  Warning: Failed to load {path.name}: {e}")
    opportunities.sort(
        key=lambda o: o.get("date_identified", ""),
        reverse=True,
    )
    return opportunities


def _load_portfolios() -> dict:
    """Load portfolio holdings from data/portfolios.json."""
    portfolio_path = Path("data/portfolios.json")
    if portfolio_path.exists():
        with open(portfolio_path) as f:
            return json.load(f)
    return {"dividend": [], "growth": []}


def _build_index(env: Environment, reports: list[dict]) -> None:
    """Build the index/search page with portfolio sections."""
    template = env.get_template("report.html")
    portfolios = _load_portfolios()
    reports_by_ticker = {r["ticker"]: r for r in reports}

    dividend_reports = [
        reports_by_ticker[t]
        for t in portfolios["dividend"]
        if t in reports_by_ticker
    ]
    dividend_reports.sort(
        key=lambda r: r.get("overall_score", 0), reverse=True
    )

    growth_reports = [
        reports_by_ticker[t]
        for t in portfolios["growth"]
        if t in reports_by_ticker
    ]
    growth_reports.sort(
        key=lambda r: r.get("overall_score", 0), reverse=True
    )

    def _avg_score(reps: list[dict]) -> float:
        scores = [r.get("overall_score", 0) for r in reps]
        return round(sum(scores) / len(scores), 1) if scores else 0

    # Collect unique sectors for filter dropdown
    sectors = sorted(
        {
            r.get("profile", {}).get("sector", "")
            for r in reports
            if r.get("profile", {}).get("sector")
        }
    )

    # Non-portfolio reports for the screener tab
    portfolio_tickers = set(portfolios["dividend"]) | set(portfolios["growth"])
    screener_reports = [r for r in reports if r["ticker"] not in portfolio_tickers]
    screener_reports.sort(key=lambda r: r.get("overall_score", 0), reverse=True)

    opportunities = _load_opportunities()

    html = template.render(
        reports=reports,
        dividend_reports=dividend_reports,
        growth_reports=growth_reports,
        screener_reports=screener_reports,
        opportunities=opportunities,
        sectors=sectors,
        dividend_avg_score=_avg_score(dividend_reports),
        growth_avg_score=_avg_score(growth_reports),
        screener_avg_score=_avg_score(screener_reports),
        total_reports=len(reports),
        generated_at=datetime.now().isoformat(),
    )
    (OUTPUT_DIR / "index.html").write_text(html)


def _build_stock_page(env: Environment, report: dict) -> None:
    """Build an individual stock report page."""
    template = env.get_template("stock_report.html")
    html = template.render(stock=report, a=report)
    ticker = report["ticker"]
    (OUTPUT_DIR / f"{ticker}.html").write_text(html)


if __name__ == "__main__":
    build_site()
