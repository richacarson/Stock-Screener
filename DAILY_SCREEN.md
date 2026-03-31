# Daily Stock Screening Task

Screen the next batch of stocks from the queue. This prompt is designed to be run as a scheduled Claude Code task.

## Step 0: Sync Reports from Prior Runs

**CRITICAL:** Each scheduled run creates its own `claude/` branch. Prior runs' reports may not be on this branch yet. Before checking the queue, pull them in:

```bash
# Fetch all remote branches first — without this, we won't see branches from prior scheduled runs
git fetch origin

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
3. Screen the next **50 stocks** (10 sequential batches of 5)
4. After all batches complete: rebuild site, commit, push, and deploy

## How to Screen Each Batch

For each batch of 5 stocks, launch **one agent at a time** (not parallel!) with this prompt.

**IMPORTANT: Batch size must be 5 (not 10, not 20).** Larger batches cause agents to hit context limits from web search results and fail mid-batch. 5 stocks × 3 web searches = 15 searches, which fits comfortably.

---

You are generating IOWN Return on Intention stock analysis reports. Generate a `reports/{TICKER}.json` file for each of the following stocks. Work through them one at a time.

### STOCKS: {comma-separated list of 5 tickers}

### WORKFLOW FOR EACH STOCK
1. Pull yfinance data: `python3 -c "from data.fetcher import fetch_stock_data; import json; d=fetch_stock_data(['TICKER']); print(json.dumps(d,indent=2))"`
2. Do 3 web searches:
   - `"{Company}" earnings revenue growth 2026` (financials, quarterly results, guidance, margins, FCF)
   - `"{Company}" CEO culture AI innovation Glassdoor AI disruption risk` (culture, AI adoption, AI threat/enabler assessment)
   - `"{Company}" ESG controversy environmental social` (ESG — NOT inspire score, that comes from CSV)
3. Look up the Inspire Impact Score from the pre-loaded inspire CSV data (do NOT web search for this)
4. Score all three dimensions (Excellence, AI Resilience, Infinite Game) per the framework
5. Write `reports/{TICKER}.json` — match the exact JSON structure of existing reports in `reports/`. Read any existing report (e.g., `reports/AAPL.json`) for the schema.

### INSPIRE SCORES (pre-loaded from CSV)
{Include the inspire score, negative_attributions, and positive_attributions for each ticker in this batch}

### SCORING RULES
- Labels: STRONG/SAFE/LOW RISK = 7+, DEVELOPING/MODERATE/NEUTRAL = 4-6, WEAK/AT RISK/HIGH RISK = 1-3
- Overall score (0-100): `avg(innovation, inspiration, infrastructure) / 10 * 50 + ai_resilience / 10 * 25 + infinite_game_overall / 10 * 25`
- Faith Alignment: displayed on report but carries **0% weight** in overall score
- Recommendation: BUY 80+, HOLD 60-79, WATCH 40-59, SELL <40
- Sleeve: Current IOWN holdings forced from `data/portfolios.json`; others: Dividend (5+ yr history, yield >2%), Growth (everything else including revenue growth >15%)
- **LIQUIDITY FLOOR**: If avg_daily_volume × stock_price < $1,000,000, Infrastructure score = 0
- **Infrastructure is calculated mechanically** from financial metrics — see SCREENING.md for the full algorithm
- Faith alignment labels: ALIGNED (>25), MIXED (-25 to 25), MISALIGNED (<-25)
- **Source references**: Use `[1]`, `[2]` etc. in analysis text. `sources` array is 1-indexed.
- **screen_date**: Use today's date in YYYY-MM-DD format.

### QUALITY STANDARDS
- Every score MUST cite specific evidence. Analysis: 2-3 dense sentences, no filler.
- Use the FULL scoring range honestly — not every company deserves 7+.
- If yfinance fails, proceed with web research only. Use null for metrics you can't find.
- Write each report to /home/user/Stock-Screener/reports/{TICKER}.json
- Process ALL 5 stocks in your batch — do not skip any.

---

## After All 10 Batches Complete

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
