# Stock Screener — Claude Code Workflow

## Overview

This is IOWN's stock screening application. It uses the **Return on Intention** framework to analyze stocks across six dimensions, generates detailed per-stock HTML reports, and deploys to GitHub Pages at https://richacarson.github.io/Stock-Screener/.

## Architecture

**Claude Code generates the analysis** — not a runtime API. The workflow:

1. Claude Code analyzes each stock using the IOWN framework
2. Analysis stored as JSON in `reports/` (e.g., `reports/AAPL.json`)
3. `python3 main.py` builds static HTML from those JSON files
4. Deploy pushes `output/` to GitHub Pages

## Quick Start

```bash
# Build the static site from existing reports
python3 main.py

# Deploy to GitHub Pages
source .env && export GITHUB_PUSH_TOKEN
python3 scripts/deploy.py
```

## IOWN Scoring Framework

Each stock is scored across five dimensions (overall /100, equally weighted at 20% each):

### Excellence Evaluation — Think Like an Owner (20%)
- **Innovation** (/10): AI adoption, digital transformation, R&D
- **Inspiration** (/10): Mission clarity, purpose, employee engagement
- **Infrastructure** (/10): Operational durability, balance sheet, legacy adaptation
  - Includes metrics table: P/E, Forward P/E, PEG, D/E, ROE, EPS/Revenue growth (YoY + 5yr CAGR), avg daily volume, dividend stats (for income stocks)
  - **HARD RULE — Liquidity Floor**: If avg_daily_volume × stock_price < $1,000,000, Infrastructure score = **0** (stock is too illiquid for IOWN to trade)

### AI Resilience (20%)
- **AI Resilience** (/10): Is AI a threat or enabler?

### Infinite Game — Sinek (20%)
- **Overall Mindset**: INFINITE / MIXED / FINITE
- Sub-scores: Just Cause, Trusting Teams, Worthy Rivals, Existential Flexibility, Courage to Lead (each /10)

### Income Quality (20%)
- **Dividend Safety** (/10): Yield, payout ratio, FCF coverage
- **RULE**: If the company does **not** pay a dividend, this section is scored as **N/A** (excluded from overall score calculation, and the remaining 4 sections are weighted 25% each)

### Faith Alignment — Inspire Insight (20%)
- **Inspire Impact Score**: -100 to +100

Plus: Recommendation (BUY/HOLD/SELL/WATCH), Investment Thesis, Key Catalysts, Key Risks.

## Report JSON Schema

Each `reports/{TICKER}.json` follows this structure:

```json
{
  "ticker": "GIS",
  "name": "General Mills, Inc.",
  "sleeve": "Prospect",
  "recommendation": "HOLD",
  "screen_date": "2026-03-09",
  "overall_score": 62,
  "excellence_evaluation": {
    "innovation": { "score": 7, "label": "STRONG", "analysis": "..." },
    "inspiration": { "score": 6, "label": "DEVELOPING", "analysis": "..." },
    "infrastructure": {
      "score": 6, "label": "DEVELOPING", "analysis": "...",
      "metrics": {
        "stock_price": 55.20,
        "pe_ratio": 9.7, "forward_pe": 13.2, "peg_ratio": 2.1,
        "debt_to_equity": 147.0, "return_on_equity": 26.8,
        "eps_growth_yoy": -4.0, "eps_growth_5yr_cagr": 2.1,
        "revenue_growth_yoy": -1.2, "revenue_growth_5yr_cagr": 3.4,
        "avg_daily_volume": 4200000,
        "dividend": {
          "yield": 5.47, "payout_ratio": 52.0,
          "consecutive_years_paid": 127, "consecutive_years_growth": 5,
          "dividend_growth_5yr_cagr": 3.8
        }
      }
    }
  },
  "ai_resilience": { "score": 7, "label": "LOW RISK", "analysis": "..." },
  "income_quality": {
    "dividend_safety": { "score": 7, "label": "SAFE", "analysis": "..." }
  },
  "infinite_game": {
    "mindset": "MIXED",
    "overall": 6,
    "summary": "...",
    "just_cause": { "score": 5, "analysis": "..." },
    "trusting_teams": { "score": 5, "analysis": "..." },
    "worthy_rivals": { "score": 6, "analysis": "..." },
    "existential_flexibility": { "score": 7, "analysis": "..." },
    "courage_to_lead": { "score": 5, "analysis": "..." }
  },
  "faith_alignment": { "inspire_impact_score": -49, "label": "MIXED" },
  "investment_thesis": "...",
  "thesis_continued": "...",
  "key_catalysts": ["...", "...", "..."],
  "key_risks": ["...", "...", "..."]
}
```

**Non-dividend companies**: Set `income_quality.dividend_safety` to `null` (not scored):
```json
"income_quality": {
  "dividend_safety": null
}
```

### Score Labels
- Sub-scores /10: **STRONG/SAFE/LOW RISK** = 7+, **DEVELOPING/MODERATE** = 4-6, **WEAK/AT RISK/HIGH RISK** = 1-3
- Sleeve: **Dividend**, **Growth**, or **Prospect**

## Generating Reports

See **SCREENING.md** for the complete step-by-step workflow. In short:

1. Pull yfinance data
2. Web research: financials, culture/leadership, AI/innovation, faith/ESG + Inspire score
3. Score all six IOWN dimensions with specific evidence
4. Calculate overall score (0-100), assign recommendation (80+ BUY, 60-79 HOLD, 40-59 WATCH, <40 SELL)
5. Assign sleeve (Dividend / Growth / Prospect)
6. Write `reports/{TICKER}.json`
7. Run `python3 main.py` to rebuild the site
8. Deploy

## Project Structure

```
Stock-Screener/
├── CLAUDE.md              # This file — workflow instructions
├── main.py                # Builds static site from reports/ JSON
├── requirements.txt       # Python dependencies
├── .env                   # GITHUB_PUSH_TOKEN (not committed)
├── reports/               # Pre-generated IOWN analysis (one JSON per stock)
│   ├── GIS.json
│   └── ...
├── screener/
│   ├── __init__.py
│   ├── filters.py         # Screening criteria and filters
│   └── rankings.py        # Sorting logic
├── data/
│   ├── __init__.py
│   └── fetcher.py         # Data fetching from Yahoo Finance
├── templates/
│   ├── report.html        # Index page — searchable stock list
│   └── stock_report.html  # Per-stock detailed IOWN report
├── output/                # Generated static site (gitignored on main)
│   ├── index.html
│   ├── {TICKER}.html
│   ├── manifest.json
│   └── reports/{TICKER}.json
├── scripts/
│   └── deploy.py          # GitHub Pages deployment script
└── .github/
    └── workflows/
        └── screen.yml     # GitHub Actions workflow
```

## Deploying to GitHub Pages

**Primary method**: Use the GitHub Git Data API to update the `gh-pages` branch directly. This bypasses `git push` restrictions in sandboxed environments (e.g., Claude Code sessions where only `claude/` branches can be pushed).

```bash
source .env && export GITHUB_PUSH_TOKEN
REPO="richacarson/Stock-Screener"
TOKEN="$GITHUB_PUSH_TOKEN"
API="https://api.github.com/repos/$REPO"

# 1. Create blobs for each output file
INDEX_CONTENT=$(base64 -w 0 output/index.html)
INDEX_SHA=$(curl -s -X POST -H "Authorization: token $TOKEN" \
  "$API/git/blobs" -d "{\"content\":\"$INDEX_CONTENT\",\"encoding\":\"base64\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['sha'])")

RESULTS_CONTENT=$(base64 -w 0 output/results.json)
RESULTS_SHA=$(curl -s -X POST -H "Authorization: token $TOKEN" \
  "$API/git/blobs" -d "{\"content\":\"$RESULTS_CONTENT\",\"encoding\":\"base64\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['sha'])")

# 2. Create tree
TREE_SHA=$(curl -s -X POST -H "Authorization: token $TOKEN" \
  "$API/git/trees" \
  -d "{\"tree\":[{\"path\":\"index.html\",\"mode\":\"100644\",\"type\":\"blob\",\"sha\":\"$INDEX_SHA\"},{\"path\":\"results.json\",\"mode\":\"100644\",\"type\":\"blob\",\"sha\":\"$RESULTS_SHA\"}]}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['sha'])")

# 3. Get current gh-pages commit (parent)
PARENT_SHA=$(curl -s -H "Authorization: token $TOKEN" \
  "$API/git/ref/heads/gh-pages" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['object']['sha'])")

# 4. Create commit
COMMIT_SHA=$(curl -s -X POST -H "Authorization: token $TOKEN" \
  "$API/git/commits" \
  -d "{\"message\":\"Deploy screener results\",\"tree\":\"$TREE_SHA\",\"parents\":[\"$PARENT_SHA\"]}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['sha'])")

# 5. Update gh-pages ref
curl -s -X PATCH -H "Authorization: token $TOKEN" \
  "$API/git/refs/heads/gh-pages" \
  -d "{\"sha\":\"$COMMIT_SHA\",\"force\":true}"
```

**Fallback method**: `python3 scripts/deploy.py` — works in local/CI environments where `git push` to `gh-pages` is allowed.

Live site: https://richacarson.github.io/Stock-Screener/

## UI Changes

Before making any UI changes to Stock-Screener, read `design.md` in the repo root. It defines the design system — follow it exactly.

## Code Style

- Python 3.10+
- Follow PEP 8
- Use type hints for function signatures
- Keep functions focused and under 50 lines where practical

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Build site
python3 main.py

# Run tests
pytest

# Format code
black .

# Lint
ruff check .
```
