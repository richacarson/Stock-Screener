# Daily Stock Screening Task

Screen the next batch of stocks from the queue. This prompt is designed to be run as a scheduled Claude Code task.

## Step 0: Sync Reports from Prior Runs

**CRITICAL:** Each scheduled run creates its own `claude/` branch. Prior runs' reports may not be on this branch yet. Before checking the queue, pull them in:

```bash
python3 -c "
import subprocess, os

result = subprocess.run(['git', 'branch', '-r'], capture_output=True, text=True)
branches = [b.strip() for b in result.stdout.splitlines()
            if 'daily-screening' in b and b.strip().startswith('origin/')]
for branch in sorted(branches):
    diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD', branch, '--', 'reports/'],
                          capture_output=True, text=True)
    new = [f for f in diff.stdout.splitlines() if f.startswith('reports/') and f.endswith('.json') and not os.path.exists(f)]
    if new:
        print(f'{branch}: pulling {len(new)} new reports')
        subprocess.run(['git', 'checkout', branch, '--'] + new)
    else:
        print(f'{branch}: no new reports')
"
git add reports/*.json 2>/dev/null
git diff --cached --quiet || git commit -m "Sync reports from prior scheduled screening runs"
```

## Instructions

1. Read `data/screening_queue.csv` to find stocks that don't yet have reports in `reports/`
2. Load `data/inspire_insight_scores.csv` into memory for inspire scores
3. Screen the next **100 stocks** (5 sequential batches of 20)
4. After all batches complete: rebuild site, commit, push, and deploy

## How to Screen Each Batch

For each batch of 20 stocks, launch **one agent at a time** (not parallel!) with this prompt:

---

You are generating IOWN Return on Intention stock analysis reports. Generate a `reports/{TICKER}.json` file for each of the following stocks. Work through them one at a time.

### STOCKS: {comma-separated list of 20 tickers}

### WORKFLOW FOR EACH STOCK
1. Pull yfinance data: `python3 -c "from data.fetcher import fetch_stock_data; import json; d=fetch_stock_data(['TICKER']); print(json.dumps(d,indent=2))"`
2. Do 3 web searches:
   - `"{Company}" earnings revenue growth 2026` (financials, quarterly results, guidance, margins, FCF)
   - `"{Company}" CEO culture AI innovation Glassdoor AI disruption risk` (culture, AI adoption, AI threat/enabler assessment)
   - `"{Company}" ESG controversy environmental social` (ESG — NOT inspire score, that comes from CSV)
3. Look up the Inspire Impact Score from the pre-loaded inspire CSV data (do NOT web search for this)
4. Score all three dimensions (Excellence, AI Resilience, Infinite Game) per the framework
5. Write `reports/{TICKER}.json`

### INSPIRE SCORES (pre-loaded from CSV)
{Include the inspire score, negative_attributions, and positive_attributions for each ticker in this batch}

### JSON SCHEMA
```json
{
  "ticker": "TICKER", "name": "Full Company Name", "sleeve": "Dividend|Growth|Prospect",
  "recommendation": "BUY|HOLD|WATCH|SELL", "screen_date": "2026-03-23", "overall_score": 62,
  "profile": { "sector": "...", "industry": "...", "exchange": "NYSE|NASDAQ", "country": "...", "website": "...", "employees": 33000, "description": "2-3 sentence company description" },
  "excellence_evaluation": {
    "innovation": { "score": 7, "label": "STRONG|DEVELOPING|WEAK", "analysis": "2-3 sentences with specific evidence" },
    "inspiration": { "score": 6, "label": "...", "analysis": "..." },
    "infrastructure": { "score": 6, "label": "...", "analysis": "...",
      "metrics": { "stock_price": 55.20, "pe_ratio": 9.7, "forward_pe": 13.2, "peg_ratio": 2.1, "debt_to_equity": 147.0, "return_on_equity": 26.8, "profit_margin": 12.5, "eps_growth_yoy": -4.0, "eps_growth_5yr_cagr": 2.1, "revenue_growth_yoy": -1.2, "revenue_growth_5yr_cagr": 3.4, "avg_daily_volume": 4200000,
        "dividend": { "yield": 5.47, "payout_ratio": 52.0, "consecutive_years_paid": 127, "consecutive_years_growth": 5, "dividend_growth_5yr_cagr": 3.8 } } } },
  "ai_resilience": { "score": 7, "label": "LOW RISK|MODERATE|HIGH RISK", "analysis": "..." },
  "infinite_game": { "mindset": "INFINITE|MIXED|FINITE", "overall": 6, "summary": "...",
    "just_cause": { "score": 5, "analysis": "..." }, "trusting_teams": { "score": 5, "analysis": "..." },
    "worthy_rivals": { "score": 6, "analysis": "..." }, "existential_flexibility": { "score": 7, "analysis": "..." },
    "courage_to_lead": { "score": 5, "analysis": "..." } },
  "faith_alignment": { "inspire_impact_score": -49, "label": "MISALIGNED", "negative_attributions": ["LGBT Activism"], "positive_attributions": ["Business Resilience", "..."], "source": "Inspire Insight" },
  "investment_thesis": "Bull case paragraph", "thesis_continued": "Bear case paragraph",
  "key_catalysts": ["specific catalyst 1", "specific catalyst 2", "specific catalyst 3"],
  "key_risks": ["specific risk 1", "specific risk 2", "specific risk 3"],
  "sources": ["Company Q1 Earnings Release, Jan 2026", "Yahoo Finance — TICKER, Mar 2026", "Analyst Report, Feb 2026"]
}
```

**Source references:** Use `[1]`, `[2]` etc. in analysis text to cite sources. `sources` array is 1-indexed. Cite financial data, analyst quotes, management commentary.

### SCORING RULES
- Labels: STRONG/SAFE/LOW RISK = 7+, DEVELOPING/MODERATE/NEUTRAL = 4-6, WEAK/AT RISK/HIGH RISK = 1-3
- Overall score (0-100) — 3 dimensions, weighted:
  - Excellence: avg(innovation, inspiration, infrastructure) / 10 * 50
  - AI Resilience: ai_resilience / 10 * 25
  - Infinite Game: infinite_game_overall / 10 * 25
- Faith Alignment: displayed on report but carries **0% weight** in overall score
- Recommendation: BUY 80+, HOLD 60-79, WATCH 40-59, SELL <40
- Sleeve: Current IOWN holdings forced from `data/portfolios.json`; others: Dividend (5+ yr history, yield >2%), Growth (revenue growth >15%), Prospect (everything else)
- **LIQUIDITY FLOOR**: If avg_daily_volume × stock_price < $1,000,000, Infrastructure score = 0
- **Infrastructure is calculated mechanically** from financial metrics — see SCREENING.md for the full algorithm
- Faith alignment: Use the inspire score and attributions provided from the CSV. Labels: ALIGNED (>25), MIXED (-25 to 25), MISALIGNED (<-25)

### QUALITY STANDARDS
- Every score MUST cite specific evidence. Analysis: 2-3 dense sentences, no filler.
- Use the FULL scoring range honestly — not every company deserves 7+.
- If yfinance fails, proceed with web research only. Use null for metrics you can't find.
- Write each report to /home/user/Stock-Screener/reports/{TICKER}.json

---

## After All 5 Batches Complete

```bash
# Rebuild site
python3 main.py

# Commit reports to the current branch
git add reports/*.json
git commit -m "Daily screening: add {N} new reports"
git push -u origin HEAD
```

## Deploy to GitHub Pages

**IMPORTANT:** Use the GitHub Git Data API to deploy — do NOT push directly to `gh-pages` or commit report files there. The `gh-pages` branch should only contain built output files (HTML, manifest.json, and copied report JSONs under `output/reports/`). Source report JSONs belong in `reports/` on the working branch.

```bash
source .env && export GITHUB_PUSH_TOKEN
python3 scripts/deploy.py
```

If `scripts/deploy.py` fails (e.g., in a sandboxed environment), use the Git Data API method documented in CLAUDE.md to deploy the contents of `output/` to `gh-pages`.

## Queue Management

The queue at `data/screening_queue.csv` has columns `symbol` and `avg_daily_volume`, sorted by volume descending. To find the next unscreened batch, check which symbols in the queue don't have a file in `reports/`. Process them in order (highest volume first).

Once all 2,202 stocks are screened, switch to REFRESH mode — re-screen the oldest reports (by `screen_date`) to keep data current.
