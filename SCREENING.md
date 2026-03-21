# IOWN Stock Screening — Report Generation Workflow

## Overview

This document defines how Claude Code generates IOWN Return on Intention stock reports. Each stock gets a `reports/{TICKER}.json` file following the schema in CLAUDE.md. The goal is institutional-quality analysis with specific data points — not generic summaries.

## Trigger

User says: "Screen {TICKER}" or "Screen {Company Name}" or provides a list of tickers.

## Step 1: Pull yfinance Data

Run the data fetcher to get live financial data:

```python
from data.fetcher import fetch_stock_data
data = fetch_stock_data(["TICKER"])
```

Key fields to capture:
- Price, market cap, P/E (trailing + forward)
- Revenue growth, earnings growth, profit margin
- Return on equity, debt-to-equity
- Average volume, recent volume, SMA-50
- Sector, industry

If yfinance fails for a ticker, proceed with web research only.

## Step 2: Web Research

Search for **four categories** of information. Be specific — the report needs real data points, not vague statements.

### 2a. Financials + Earnings
Search for: `"{Company Name}" earnings {current year}`, `"{Company Name}" revenue guidance`
- Most recent quarterly results (revenue, EPS, YoY changes)
- Forward guidance and analyst consensus
- Margin trends (expanding or compressing?)
- FCF generation and capital allocation priorities
- Any recent acquisitions, divestitures, or restructuring

### 2b. Culture + Leadership
Search for: `"{Company Name}" Glassdoor reviews`, `"{Company Name}" CEO strategy`, `"{Company Name}" layoffs`
- Glassdoor overall rating and key themes from reviews
- CEO's stated vision and strategy (from recent interviews, earnings calls)
- Employee sentiment: DEI ratings, work-life balance, leadership trust
- Recent layoff history or hiring trends
- Any cultural controversies or notable employee engagement data

### 2c. AI / Innovation + Moat
Search for: `"{Company Name}" AI artificial intelligence`, `"{Company Name}" digital transformation`, `"{Company Name}" competitive advantage`
- AI adoption: specific tools, partnerships, savings achieved
- R&D investment and innovation pipeline
- Digital transformation initiatives
- Competitive moat: brand strength, market share, distribution advantages, switching costs
- Disruption risk: is AI a threat or enabler for this business?

### 2d. Faith / ESG + Inspire Score
Search for: `"{Company Name}" site:inspireinsight.com`, `"{Company Name}" Inspire Investing score`, `"{Company Name}" ESG controversy`
- Inspire Impact Score from inspireinsight.com (look for the actual numeric score)
- ESG controversies or notable positive impact
- Faith-based alignment factors
- If Inspire score not found, search more broadly and note that the score is estimated

## Step 3: Score Each Dimension

Use the research to score each dimension. Every score MUST be justified by specific data from the research — never assign a score without citing evidence.

### Excellence Evaluation — Think Like an Owner (30% of overall)

**Innovation** (/10):
- 8-10: Active AI deployment with measurable results, significant R&D, product innovation leadership
- 5-7: Some digital transformation, incremental innovation, AI exploration
- 1-4: Legacy operations, minimal R&D, no meaningful AI adoption

**Inspiration** (/10):
- 8-10: Clear transformational mission, high employee engagement (Glassdoor 4.2+), strong purpose alignment
- 5-7: Decent mission statement, moderate engagement (Glassdoor 3.5-4.1), some purpose connection
- 1-4: Generic or absent mission, low engagement (Glassdoor <3.5), cultural issues

**Infrastructure** (/10):
- 8-10: Strong balance sheet, long operating history, proven adaptability, dividend aristocrat
- 5-7: Adequate balance sheet, some legacy challenges, moderate dividend history
- 1-4: Weak balance sheet, high debt, no dividend, structural vulnerabilities

### Risk, Moat & Erosion (25% of overall)

**AI Resilience** (/10):
- 8-10 (LOW RISK): AI enhances the business model, company is actively deploying AI
- 5-7 (MODERATE): Mixed — some AI benefit, some disruption risk
- 1-4 (HIGH RISK): AI threatens core business model, company is slow to adapt

**Moat Strength** (/10):
- 8-10 (STRONG): Multiple durable advantages (brand, scale, network effects, switching costs, patents)
- 5-7 (MODERATE): Some competitive advantages but facing erosion
- 1-4 (WEAK): Commodity business, low barriers, intense competition

**Erosion Protection** (/10):
- 8-10 (STRONG): Growing margins, strong FCF, sustainable payout, gaining market share
- 5-7 (MODERATE): Stable margins, adequate FCF, some competitive pressure
- 1-4 (WEAK): Declining margins, FCF pressure, market share losses, dividend at risk

### Social Arbitrage — Camillo Lens (10% of overall)

**Social Arbitrage** (/10):
- 8-10 (STRONG): Clear mispricing — market sentiment significantly worse than fundamentals warrant, or a social/consumer trend the market hasn't priced in
- 5-7 (NEUTRAL): Fairly priced — no significant gap between sentiment and fundamentals
- 1-4 (WEAK): Overpriced — market sentiment more optimistic than fundamentals support

### Income Quality (10% of overall)

**Dividend Safety** (/10):
- 8-10 (SAFE): Long dividend history, low payout ratio (<60%), growing FCF, dividend growth streak
- 5-7 (MODERATE): Adequate coverage but some pressure, payout ratio 60-80%, stable dividend
- 1-4 (AT RISK): High payout ratio (>80%), declining FCF, dividend cut risk, no dividend history
- For non-dividend-paying stocks: Score based on FCF generation quality and likelihood of future shareholder returns

### Infinite Game — Sinek (20% of overall)

Rate the **overall mindset** (INFINITE / MIXED / FINITE) and provide an overall score /10.

Then score each sub-dimension /10:

**Just Cause**: Does the company have a cause bigger than itself? Is the mission existential or just marketing?

**Trusting Teams**: Does leadership create psychological safety? What do employees say (Glassdoor)? Are there recurring layoffs?

**Worthy Rivals**: Does the company learn from competitors or just try to "beat" them? Is the language about winning or improving?

**Existential Flexibility**: Has the company made dramatic strategic pivots when needed? Does it cling to legacy or adapt?

**Courage to Lead**: Does leadership make decisions for the long term even when short-term costly? Or do quarterly pressures dominate?

### Faith Alignment — Inspire Insight (5% of overall)

**Inspire Impact Score**: Use the score from inspireinsight.com. If unavailable, estimate based on:
- Positive: Faith-aligned values, no controversial products, positive community impact
- Negative: Products/services that conflict with faith-based values, major ESG controversies
- Range: -100 to +100
- Label: ALIGNED (score > 25), MIXED (-25 to 25), MISALIGNED (score < -25)

## Step 4: Calculate Overall Score

Weighted composite (0-100):

```
overall = (
    (innovation + inspiration + infrastructure) / 30 * 100 * 0.30  # Excellence: 30%
  + (ai_resilience + moat_strength + erosion_protection) / 30 * 100 * 0.25  # Risk/Moat: 25%
  + infinite_game_overall / 10 * 100 * 0.20  # Infinite Game: 20%
  + dividend_safety / 10 * 100 * 0.10  # Income: 10%
  + social_arbitrage / 10 * 100 * 0.10  # Arbitrage: 10%
  + (inspire_impact_score + 100) / 200 * 100 * 0.05  # Faith: 5%
)
```

Round to nearest integer.

## Step 5: Assign Recommendation

Based on overall score:
- **BUY**: 80+
- **HOLD**: 60-79
- **WATCH**: 40-59
- **SELL**: <40

## Step 6: Assign Sleeve

Based on company characteristics:
- **Dividend**: Established dividend payer with 5+ year history, yield > 2%, stable payout
- **Growth**: Revenue growth > 15%, or high-growth sector with strong momentum, may or may not pay dividend
- **Prospect**: Under evaluation, doesn't clearly fit Dividend or Growth, or new to the IOWN universe

## Step 7: Write the Report

Generate `reports/{TICKER}.json` following the schema in CLAUDE.md.

### Quality Standards

1. **Every score must cite specific evidence** — "Glassdoor 3.9/5", "52% payout ratio", "127-year dividend history", not "good culture" or "strong dividends"
2. **Analysis paragraphs are 2-3 sentences** — dense with data, no filler
3. **Investment thesis is two paragraphs** — first the bull case, second the bear case with nuance
4. **Key catalysts and risks are specific and actionable** — not generic "market downturn" but "secular decline in core cereal category as consumers shift to fresh/less-processed alternatives"
5. **Scores should be honest** — not every company deserves 7+. A score of 4-5 is developing, not a failure. Use the full range.

### Label Reference

| Score | Labels |
|-------|--------|
| 7-10 | STRONG, SAFE, LOW RISK |
| 4-6 | DEVELOPING, MODERATE, NEUTRAL |
| 1-3 | WEAK, AT RISK, HIGH RISK |

## Step 8: Build and Verify

After generating reports, rebuild the site:

```bash
python3 main.py
```

Verify the generated HTML looks correct, then deploy per CLAUDE.md instructions.

## Batch Processing

When screening multiple stocks:
1. Process one stock at a time through the full workflow
2. Commit each report individually or in small batches (5-10)
3. Rebuild the site after each batch
4. Deploy after each batch is verified

## Example Session

```
User: Screen AAPL

Claude Code:
1. Pulls yfinance data for AAPL
2. Web searches: "Apple earnings 2026", "Apple Glassdoor reviews",
   "Apple AI artificial intelligence", "Apple site:inspireinsight.com"
3. Scores all dimensions with specific evidence
4. Calculates overall: 85/100 → BUY
5. Assigns sleeve: Growth
6. Writes reports/AAPL.json
7. Runs python3 main.py
8. Deploys to GitHub Pages
```
