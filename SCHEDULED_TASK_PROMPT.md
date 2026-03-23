# IOWN Stock Screener — Daily Screening Task

You are running a scheduled daily task for the IOWN Stock Screener project at `/home/user/Stock-Screener`. Your job is to generate IOWN Return on Intention stock analysis reports for the next batch of stocks.

**Two modes:** If unscreened stocks remain in the queue, screen those first. Once the entire queue is screened, cycle back and **re-screen the oldest reports** (by `screen_date`) to keep data fresh.

## Step 1: Determine What to Screen

Run this Python script to find the next 100 stocks to screen:

```bash
python3 -c "
import csv, os, json
from datetime import datetime

# Load queue (sorted by avg daily volume descending)
with open('data/screening_queue.csv') as f:
    queue = list(csv.DictReader(f))
queue_tickers = {r['symbol'] for r in queue}
queue_lookup = {r['symbol']: r for r in queue}

# Find which tickers already have reports
report_files = [f for f in os.listdir('reports') if f.endswith('.json')]
done = {f.replace('.json','') for f in report_files}

# Mode 1: Unscreened stocks remain
remaining = [r for r in queue if r['symbol'] not in done]

if remaining:
    batch_tickers = [r['symbol'] for r in remaining[:100]]
    mode = 'NEW'
    print(f'MODE: Screening NEW stocks')
    print(f'Total in queue: {len(queue)}')
    print(f'Already screened: {len(done)}')
    print(f'Remaining unscreened: {len(remaining)}')
else:
    # Mode 2: All screened — re-screen oldest reports
    report_dates = []
    for rf in report_files:
        ticker = rf.replace('.json','')
        if ticker not in queue_tickers:
            continue
        with open(f'reports/{rf}') as fh:
            try:
                data = json.load(fh)
                sd = data.get('screen_date', '2000-01-01')
                report_dates.append((ticker, sd))
            except:
                report_dates.append((ticker, '2000-01-01'))
    report_dates.sort(key=lambda x: x[1])  # oldest first
    batch_tickers = [t for t, _ in report_dates[:100]]
    oldest_date = report_dates[0][1] if report_dates else 'N/A'
    newest_in_batch = report_dates[min(99, len(report_dates)-1)][1] if report_dates else 'N/A'
    mode = 'REFRESH'
    print(f'MODE: Re-screening OLDEST reports (all {len(queue)} stocks already screened)')
    print(f'Oldest report in batch: {oldest_date}')
    print(f'Newest report in batch: {newest_in_batch}')

print(f'This batch: {len(batch_tickers)} stocks')
print()

# Load inspire data
with open('data/inspire_insight_scores.csv', encoding='utf-8-sig') as f:
    inspire = {r['ticker']: r for r in csv.DictReader(f)}

# Print batches of 20 with inspire data
for i in range(0, len(batch_tickers), 20):
    chunk = batch_tickers[i:i+20]
    print(f'=== BATCH {i//20 + 1} ({len(chunk)} stocks) ===')
    for t in chunk:
        stock = queue_lookup.get(t, {})
        vol = stock.get('avg_daily_volume', 'N/A')
        insp = inspire.get(t, {})
        score = insp.get('score', '0')
        neg = insp.get('negative_attributions', '').strip()
        pos = insp.get('positive_attributions', '').strip()
        print(f'{t} | vol={vol} | inspire={score} | neg=[{neg}] | pos=[{pos}]')
    print()
"
```

## Step 2: Screen Each Batch

Process **5 batches of 20 stocks each**, launching agents **ONE AT A TIME** (never parallel). Wait for each agent to complete before starting the next.

For each batch, launch an agent with the prompt below, filling in the stock list and inspire data from Step 1's output:

---

### Agent Prompt Template

You are generating IOWN Return on Intention stock analysis reports. Generate a `reports/{TICKER}.json` file for each of the following stocks. Work through them one at a time.

#### YOUR STOCKS (Batch N)
{List each ticker, e.g.: BAC, BBD, AMD, ...}

#### INSPIRE SCORES (from CSV — do NOT web search for these)
{For each ticker, paste the inspire score and attributions from Step 1 output, e.g.:
- BAC: score=-67, neg=[Abortion Activism | LGBT Activism], pos=[Air Quality | Business Resilience | Customer Privacy | ...]
- BBD: score=-49, neg=[LGBT Activism], pos=[Business Resilience | ...]
}

#### WORKFLOW FOR EACH STOCK
1. Pull yfinance data:
   ```
   python3 -c "from data.fetcher import fetch_stock_data; import json; d=fetch_stock_data(['TICKER']); print(json.dumps(d,indent=2))"
   ```
2. Do **3 web searches** (NOT 4 — inspire comes from CSV above):
   - `"{Company Name}" earnings revenue growth 2026` — financials, quarterly results, guidance, margins, FCF
   - `"{Company Name}" CEO leadership culture Glassdoor AI innovation AI disruption risk` — culture, employee sentiment, AI adoption, AI threat/enabler assessment
   - `"{Company Name}" ESG controversy environmental social governance` — ESG issues, community impact (NOT inspire score)
3. Score all three dimensions (Excellence, AI Resilience, Infinite Game) using research evidence
4. Use the inspire score and attributions provided above for `faith_alignment` (do NOT guess or web search)
5. Write `reports/{TICKER}.json`

#### JSON SCHEMA (every report must match this exactly)
```json
{
  "ticker": "TICKER",
  "name": "Full Company Name",
  "sleeve": "Dividend|Growth|Prospect",
  "recommendation": "BUY|HOLD|WATCH|SELL",
  "screen_date": "YYYY-MM-DD",
  "overall_score": 62,
  "profile": {
    "sector": "...",
    "industry": "...",
    "exchange": "NYSE|NASDAQ",
    "country": "...",
    "website": "https://...",
    "employees": 33000,
    "description": "2-3 sentence company description"
  },
  "excellence_evaluation": {
    "innovation": {
      "score": 7,
      "label": "STRONG|DEVELOPING|WEAK",
      "analysis": "2-3 sentences citing specific evidence"
    },
    "inspiration": {
      "score": 6,
      "label": "STRONG|DEVELOPING|WEAK",
      "analysis": "2-3 sentences citing specific evidence"
    },
    "infrastructure": {
      "score": 6,
      "label": "STRONG|DEVELOPING|WEAK",
      "analysis": "2-3 sentences citing specific evidence",
      "metrics": {
        "stock_price": 55.20,
        "pe_ratio": 9.7,
        "forward_pe": 13.2,
        "peg_ratio": 2.1,
        "debt_to_equity": 147.0,
        "return_on_equity": 26.8,
        "profit_margin": 12.5,
        "eps_growth_yoy": -4.0,
        "eps_growth_5yr_cagr": 2.1,
        "revenue_growth_yoy": -1.2,
        "revenue_growth_5yr_cagr": 3.4,
        "avg_daily_volume": 4200000,
        "dividend": {
          "yield": 5.47,
          "payout_ratio": 52.0,
          "consecutive_years_paid": 127,
          "consecutive_years_growth": 5,
          "dividend_growth_5yr_cagr": 3.8
        }
      }
    }
  },
  "ai_resilience": {
    "score": 7,
    "label": "LOW RISK|MODERATE|HIGH RISK",
    "analysis": "2-3 sentences citing specific evidence"
  },
  "infinite_game": {
    "mindset": "INFINITE|MIXED|FINITE",
    "overall": 6,
    "summary": "2-3 sentence summary of infinite game assessment",
    "just_cause": { "score": 5, "analysis": "..." },
    "trusting_teams": { "score": 5, "analysis": "..." },
    "worthy_rivals": { "score": 6, "analysis": "..." },
    "existential_flexibility": { "score": 7, "analysis": "..." },
    "courage_to_lead": { "score": 5, "analysis": "..." }
  },
  "faith_alignment": {
    "inspire_impact_score": -49,
    "label": "MISALIGNED",
    "negative_attributions": ["LGBT Activism"],
    "positive_attributions": ["Business Resilience", "Customer Privacy", "..."],
    "source": "Inspire Insight"
  },
  "investment_thesis": "Bull case paragraph with specific data points",
  "thesis_continued": "Bear case paragraph with specific risks and nuance",
  "key_catalysts": [
    "Specific catalyst 1 with timeframe",
    "Specific catalyst 2 with data",
    "Specific catalyst 3 with trigger"
  ],
  "key_risks": [
    "Specific risk 1 with quantification",
    "Specific risk 2 with trigger scenario",
    "Specific risk 3 with impact assessment"
  ]
}
```

#### SCORING RULES

**Sub-score labels (/10):**
- 7-10: STRONG, SAFE, LOW RISK
- 4-6: DEVELOPING, MODERATE, NEUTRAL
- 1-3: WEAK, AT RISK, HIGH RISK

**Overall score (0-100) — 3 dimensions, weighted:**
```
overall = (
    avg(innovation, inspiration, infrastructure) / 10 * 50   # Excellence: 50%
  + ai_resilience / 10 * 25                                   # AI Resilience: 25%
  + infinite_game_overall / 10 * 25                            # Infinite Game: 25%
)
```
Faith Alignment is displayed on the report but carries **0% weight** in the overall score.
No special handling for non-dividend stocks — same formula for all. Dividend metrics factor into Infrastructure sub-score (see SCREENING.md).

**Recommendation from overall score:**
- **BUY**: 80+
- **HOLD**: 60-79
- **WATCH**: 40-59
- **SELL**: <40

**Sleeve assignment:**
- **Current IOWN holdings** (in `data/portfolios.json`): Force sleeve from portfolios.json (dividend array → "Dividend", growth array → "Growth")
- **All other stocks**: Dividend (5+ yr history AND yield > 2%), Growth (revenue growth > 15% YoY), Prospect (everything else)

**HARD RULES:**
- **LIQUIDITY FLOOR**: If `avg_daily_volume × stock_price < $1,000,000` → Infrastructure score = **0**
- **Infrastructure is calculated mechanically** from financial metrics — see SCREENING.md for the full algorithm
- **Faith alignment labels**: ALIGNED (score > 25), MIXED (-25 to 25), MISALIGNED (score < -25)
- **Inspire data**: MUST come from the CSV data provided above. Do NOT web search for inspire scores.

**screen_date**: Use today's date in YYYY-MM-DD format.

#### QUALITY STANDARDS
- Every score MUST cite specific evidence from research. No generic statements.
- Analysis: 2-3 dense sentences per field, no filler words.
- Use the FULL scoring range honestly — a score of 3-4 is appropriate for struggling companies.
- Investment thesis: first paragraph is bull case, second is bear case. Both cite specific data.
- Key catalysts and risks: specific and actionable, not generic "market downturn" platitudes.
- If yfinance fails for a ticker, proceed with web research only. Use `null` for unavailable metrics.
- Write each report to `/home/user/Stock-Screener/reports/{TICKER}.json`
- Process ALL 20 stocks in your batch — do not skip any.

---

## Step 3: After All Batches Complete

Once all 5 agents have finished (or however many batches were needed for this run):

```bash
# Rebuild the static site from all reports
python3 main.py

# Stage and commit
git add reports/*.json

# Use appropriate commit message based on mode (NEW or REFRESH)
# Replace N with actual count and adjust message accordingly:
# For NEW mode:
git commit -m "Daily screening: add N new IOWN reports

Screened next batch from screening queue. Reports include
web-researched analysis with Inspire Insight scores from CSV."

# For REFRESH mode:
git commit -m "Daily screening: refresh N oldest IOWN reports

Re-screened oldest reports with updated financials and research.
All queue stocks already covered — cycling through for freshness."

# Push to remote
git push
```

## Step 4: Deploy to GitHub Pages

After committing, deploy the updated site:

```bash
source .env && export GITHUB_PUSH_TOKEN
python3 scripts/deploy.py
```

## Step 5: Report Results

After deploying, print a summary:
```bash
python3 -c "
import csv, os, json
from datetime import datetime

with open('data/screening_queue.csv') as f:
    queue = list(csv.DictReader(f))
queue_tickers = {r['symbol'] for r in queue}
done = {f.replace('.json','') for f in os.listdir('reports') if f.endswith('.json')}
remaining = [r for r in queue if r['symbol'] not in done]

# Find oldest report date
oldest_date = None
for rf in os.listdir('reports'):
    if not rf.endswith('.json'): continue
    t = rf.replace('.json','')
    if t not in queue_tickers: continue
    try:
        with open(f'reports/{rf}') as fh:
            sd = json.load(fh).get('screen_date','')
            if oldest_date is None or sd < oldest_date:
                oldest_date = sd
    except: pass

print(f'Reports total: {len(done)}')
print(f'Queue remaining (unscreened): {len(remaining)}')
if remaining:
    print(f'Estimated days to finish first pass: {len(remaining) // 100 + (1 if len(remaining) % 100 else 0)}')
else:
    print(f'All stocks screened! Now in REFRESH mode (re-screening oldest first)')
print(f'Oldest report date: {oldest_date or \"N/A\"}')
print(f'Full refresh cycle: ~{len(queue) // 100 + 1} days')
"
```

## Important Notes

- **NEVER launch agents in parallel** — sequential only (one at a time) to avoid rate limits
- **NEVER web search for Inspire scores** — always use the CSV data
- **Always use today's date** for `screen_date`
- If a batch agent fails or times out, note which stocks were missed and include them in the next batch
- The queue is sorted by avg daily volume descending — always process in queue order (most liquid first)
