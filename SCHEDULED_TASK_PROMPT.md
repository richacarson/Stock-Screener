# IOWN Stock Screener — Daily Screening Task

You are running a scheduled daily task for the IOWN Stock Screener project at `/home/user/Stock-Screener`. Your job is to generate IOWN Return on Intention stock analysis reports for the next batch of unscreened stocks.

## Step 1: Determine What to Screen

Run this Python script to find the next 100 unscreened stocks from the queue:

```bash
python3 -c "
import csv, os, json

# Load queue (sorted by avg daily volume descending)
with open('data/screening_queue.csv') as f:
    queue = list(csv.DictReader(f))

# Find which tickers already have reports
done = {f.replace('.json','') for f in os.listdir('reports') if f.endswith('.json')}

# Get next unscreened tickers
remaining = [r for r in queue if r['ticker'] not in done]
batch = remaining[:100]

print(f'Total in queue: {len(queue)}')
print(f'Already screened: {len(done)}')
print(f'Remaining: {len(remaining)}')
print(f'This batch: {len(batch)} stocks')
print()

# Load inspire data
with open('data/inspire_insight_scores.csv', encoding='utf-8-sig') as f:
    inspire = {r['ticker']: r for r in csv.DictReader(f)}

# Print batches of 20 with inspire data
for i in range(0, len(batch), 20):
    chunk = batch[i:i+20]
    print(f'=== BATCH {i//20 + 1} ({len(chunk)} stocks) ===')
    for stock in chunk:
        t = stock['ticker']
        insp = inspire.get(t, {})
        score = insp.get('score', '0')
        neg = insp.get('negative_attributions', '').strip()
        pos = insp.get('positive_attributions', '').strip()
        print(f'{t} | {stock[\"name\"]} | vol={stock[\"avg_daily_volume\"]} | inspire={score} | neg=[{neg}] | pos=[{pos}]')
    print()
"
```

If the output says "Remaining: 0", all stocks are screened — skip to Step 4 (build and deploy).

## Step 2: Screen Each Batch

Process **5 batches of 20 stocks each**, launching agents **ONE AT A TIME** (never parallel). Wait for each agent to complete before starting the next.

For each batch, launch an agent with the prompt below, filling in the stock list and inspire data from Step 1's output:

---

### Agent Prompt Template

You are generating IOWN Return on Intention stock analysis reports. Generate a `reports/{TICKER}.json` file for each of the following stocks. Work through them one at a time.

#### YOUR STOCKS (Batch N)
{List each ticker with company name, e.g.: BAC (Bank of America), BBD (Banco Bradesco), AMD (Advanced Micro Devices), ...}

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
   - `"{Company Name}" CEO leadership culture Glassdoor AI innovation` — culture, employee sentiment, AI adoption, R&D, competitive moat
   - `"{Company Name}" ESG controversy environmental social governance` — ESG issues, community impact (NOT inspire score)
3. Score all dimensions using research evidence
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
  "income_quality": {
    "dividend_safety": {
      "score": 7,
      "label": "SAFE|MODERATE|AT RISK",
      "analysis": "2-3 sentences citing specific evidence"
    }
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
- 4-6: DEVELOPING, MODERATE
- 1-3: WEAK, AT RISK, HIGH RISK

**Overall score (0-100) — 5 dimensions, each weighted 20%:**
```
overall = (
    avg(innovation, inspiration, infrastructure) / 10 * 20     # Excellence: 20%
  + ai_resilience / 10 * 20                                    # AI Resilience: 20%
  + infinite_game_overall / 10 * 20                             # Infinite Game: 20%
  + dividend_safety / 10 * 20                                   # Income Quality: 20%
  + (inspire_impact_score + 100) / 200 * 20                     # Faith: 20%
)
```
**If the company does NOT pay a dividend:** Set `"dividend_safety": null`. The remaining 4 dimensions are weighted 25% each (multiply the 4-dimension sum by 100/80).

**Recommendation from overall score:**
- **BUY**: 80+
- **HOLD**: 60-79
- **WATCH**: 40-59
- **SELL**: <40

**Sleeve assignment:**
- **Dividend**: Established dividend payer with 5+ year history AND yield > 2%
- **Growth**: Revenue growth > 15% YoY
- **Prospect**: Everything else

**HARD RULES:**
- **LIQUIDITY FLOOR**: If `avg_daily_volume × stock_price < $1,000,000` → Infrastructure score = **0**
- **Non-dividend stocks**: Set dividend metrics (yield, payout_ratio, dividend_growth_5yr_cagr) to `null`, consecutive fields to `0`
- **Dividend safety scoring**: Based on 5YR dividend growth CAGR beating inflation (~3%), high consecutive years of payments, and consecutive years of growth. Yield is **NOT** a factor in dividend safety scoring.
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

# Stage and commit new reports
git add reports/*.json
git commit -m "Daily screening: add N new IOWN reports

Screened next batch from screening queue. Reports include
web-researched analysis with Inspire Insight scores from CSV."

# Push to remote
git push
```

## Step 4: Report Results

After committing, print a summary:
```bash
python3 -c "
import csv, os
with open('data/screening_queue.csv') as f:
    queue = list(csv.DictReader(f))
done = {f.replace('.json','') for f in os.listdir('reports') if f.endswith('.json')}
remaining = [r for r in queue if r['ticker'] not in done]
print(f'Reports total: {len(done)}')
print(f'Queue remaining: {len(remaining)}')
print(f'Estimated days to complete: {len(remaining) // 100 + (1 if len(remaining) % 100 else 0)}')
"
```

## Important Notes

- **NEVER launch agents in parallel** — sequential only (one at a time) to avoid rate limits
- **NEVER web search for Inspire scores** — always use the CSV data
- **Always use today's date** for `screen_date`
- If a batch agent fails or times out, note which stocks were missed and include them in the next batch
- The queue is sorted by avg daily volume descending — always process in queue order (most liquid first)
