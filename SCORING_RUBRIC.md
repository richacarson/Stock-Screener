# IOWN Stock Screener — Scoring Rubric v2

## Overview

This document defines exactly how Claude Code scores stocks in the IOWN Return on Intention framework. It replaces all scoring logic previously defined in SCREENING.md and the scoring sections of CLAUDE.md / SCHEDULED_TASK_PROMPT.md / DAILY_SCREEN.md.

**Three dimensions. No ambiguity.**

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Excellence Evaluation | 50% | Innovation + Inspiration + Infrastructure (Think Like an Owner) |
| AI Resilience | 25% | Is AI a threat or an enabler for this business? |
| Infinite Game | 25% | Does this company play to keep playing, or play to win this quarter? |

Faith Alignment (Inspire Insight) is **displayed on the report but carries 0% weight** in the overall score.

Social Arbitrage, Moat Strength, and Erosion Protection are **removed entirely** — they are not scored, not displayed, and not referenced.

---

## Overall Score Formula

```
overall_score = (
    avg(innovation, inspiration, infrastructure) / 10 * 50    # Excellence: 50%
  + ai_resilience / 10 * 25                                    # AI Resilience: 25%
  + infinite_game_overall / 10 * 25                             # Infinite Game: 25%
)
```

Round to nearest integer. Range: 0–100.

**There is no special handling for non-dividend stocks.** Every stock uses the same formula with the same weights. Dividend metrics factor into the Infrastructure sub-score (see below), but the overall weight structure is identical for all stocks.

---

## Recommendation Thresholds

| Score | Recommendation |
|-------|---------------|
| 80+ | BUY |
| 60–79 | HOLD |
| 40–59 | WATCH |
| <40 | SELL |

---

## Sleeve Assignment

**For current IOWN holdings** (tickers listed in `data/portfolios.json`): Force the sleeve from portfolios.json. If a ticker is in the `dividend` array, sleeve = "Dividend". If in the `growth` array, sleeve = "Growth". Do not override based on stock characteristics.

**For all other stocks** (prospects / screen universe): Auto-classify:
- **Dividend**: Established dividend payer with 5+ year payment history AND yield > 2%
- **Growth**: Revenue growth > 15% YoY
- **Growth**: Everything else (default)

---

## Dimension 1: Excellence Evaluation (50% of overall)

Three sub-scores, each /10. The Excellence score is the simple average of the three.

### 1A. Innovation (/10) — Structured Evidence Checklist

Innovation measures whether the company is building the future or coasting on the past. This is scored using a **weighted evidence checklist**. Claude Code must search for specific evidence on each item and score based on what it finds.

**Calibration anchor:** NVDA = 10 (dominant AI ecosystem, full-stack innovation from chips to networking to software to frameworks, defines the frontier of AI computing, CUDA ecosystem built 17 years before the AI boom, successful pivots from gaming → crypto → AI).

#### Evidence Items (max 10 points)

| # | Evidence Item | Max Points | 0 points | 1 point | 2 points | 3 points |
|---|--------------|------------|----------|---------|----------|----------|
| 1 | **Innovation Track Record** — Successful product launches, market pivots, or business model transformations in the last 5 years | **3** | No meaningful new products or pivots; business looks the same as 5 years ago | One modest product refresh or incremental extension | One significant launch or pivot that opened a new revenue stream | Multiple successful launches or a transformative pivot that redefined the company (e.g., NVDA gaming→AI) |
| 2 | **AI Deployment with Measurable Results** — Shipping AI-powered products to customers, or reporting specific AI-driven cost savings/revenue gains internally | **2** | No AI deployment or strategy evident | AI "exploration" announced but no products shipping or savings reported | AI products shipping to customers OR specific internal savings quantified (e.g., "$50M in efficiency gains from AI") |  |
| 3 | **Market Share Leadership** — Dominant or gaining share in a category they are defining or leading | **2** | Commodity participant with no share differentiation | Meaningful player but not a leader; stable share | Category leader or fastest share gainer with specific data (e.g., "90% AI chip market share", "gained 400bps of share in 2025") |  |
| 4 | **Product Pipeline** — Next-generation products announced with specific timelines and visibility | **2** | No pipeline visibility; no next-gen products discussed | General R&D activity but vague timelines; "we're working on next-gen" | Specific next-gen products named with launch dates and revenue visibility (e.g., "Rubin platform launching H2 2026 with $500B pipeline") |  |
| 5 | **R&D Intensity** — R&D spending as a percentage of revenue relative to industry peers | **1** | Below industry average R&D spend | At or near industry average | Above industry average (top quartile for sector) |  |

**Innovation score = sum of points across all 5 items.** Max 10.

#### Scoring Rules

- Claude Code must search for evidence on ALL five items. If evidence is not found after searching, the item scores 0.
- Every non-zero score must cite specific evidence in the analysis paragraph (company names, dollar amounts, percentages, product names, dates).
- Item 1 (Innovation Track Record) is worth 3 points because IOWN values proven execution over promises. A company that has successfully reinvented itself earns more than a company that merely talks about innovation.

### 1B. Inspiration (/10) — Mission Floor + Evidence Adds

Inspiration measures whether the company has a genuine purpose beyond profit, whether leadership is aligned with that purpose, and whether the organization lives it out. This is scored using a **mission quality floor** plus **evidence-based additions**.

**Calibration anchor:** NVDA = 10 (Jensen Huang: 32-year tenure leading NVIDIA through gaming, crypto, and AI eras; mission to "accelerate computing for the world's most important challenges" is validated by decades of execution; company culture is widely cited as a competitive advantage).

**Note:** A true 10 on Inspiration is rare. It requires a deeply articulated mission that is clearly lived out, PLUS strong evidence across community impact, employee retention, and insider conviction. Most excellent companies score 6–8.

#### Part A: Mission Quality Floor (0–4 points)

Claude Code must visit the company's website (or find the mission/purpose/vision statement via web search) and evaluate it.

| Points | Mission Quality |
|--------|----------------|
| 0 | **No mission, purpose, or vision statement found** on the company's website or public materials. The company does not articulate why it exists beyond making money. |
| 1 | **Generic or boilerplate mission.** Exists but is interchangeable with any company in the industry. Examples: "We deliver value to our shareholders and customers." "We strive to be the best in our industry." |
| 2 | **Clear but not distinctive.** The mission identifies what the company does and for whom, but doesn't articulate a deeper purpose or inspire beyond the obvious. Examples: "We provide innovative healthcare solutions to improve patient outcomes." |
| 3 | **Specific and thoughtful.** The mission reflects genuine intentionality — it's clearly been thought through, connects the company's work to a larger purpose, and differentiates from peers. You can tell leadership spent time on this. |
| 4 | **Transformative and validated by execution.** The mission is not just well-written — it has been proven out by decades of consistent strategic decisions. The purpose IS the competitive advantage. Examples: NVDA's "accelerate computing" validated by 17 years of CUDA investment before the AI boom. |

#### Part B: Evidence Additions (0–6 points, max 2 each)

| # | Evidence Item | Max Points | 0 points | 1 point | 2 points |
|---|--------------|------------|----------|---------|----------|
| 1 | **Community & Charitable Impact** — Does the company give back beyond profit? Foundation, charitable programs, community investment aligned with Kingdom-building values. | **2** | No evidence of charitable giving or community programs | General corporate philanthropy or matching programs | Significant, distinctive community investment with specific programs and dollar amounts cited (e.g., company foundation, employee volunteer programs with measurable impact, community development initiatives) |
| 2 | **Employee Retention & Tenure** — Do people stay because they believe in the mission? Low voluntary turnover, long average tenure, or evidence that employees cite purpose/mission as why they stay. | **2** | High turnover, frequent layoffs, or no retention data available | Average retention for the industry; no standout data either way | Evidence of above-average retention, long employee tenure, or specific data showing employees stay for the mission (e.g., "average tenure 12 years", "voluntary turnover below 5%") |
| 3 | **Insider Buying** — Are leaders putting their own money in? Net insider buying vs. selling in the last 12 months signals that leadership believes in the long-term story. | **2** | Net insider selling or no insider transaction data | Neutral — minimal insider transactions or roughly balanced buying/selling | Meaningful net insider buying by CEO or multiple executives in the last 12 months with specific dollar amounts |

#### Inspiration Score

```
inspiration_score = mission_floor + community_impact + employee_retention + insider_buying
```

Max: 4 + 2 + 2 + 2 = **10**

#### Scoring Rules

- Claude Code must search for the company's mission/vision/purpose statement on their website.
- Claude Code must search for insider buying/selling data.
- Claude Code must search for community/charitable programs.
- Employee retention data is often hard to find — if no data exists after searching, score 0 on that item. Do not guess.
- Every non-zero score must cite specific evidence in the analysis paragraph.
- Do NOT use Glassdoor ratings, ESG scores, or DEI metrics as Inspiration evidence.

### 1C. Infrastructure (/10) — Quantitative

Infrastructure measures financial durability, balance sheet strength, growth profile, and (for dividend payers) income quality. **This dimension is scored mechanically using distance-from-target on specific financial metrics.** Claude Code does NOT assign this score based on vibes — it calculates it.

#### Metrics and Targets

All stocks are scored on these **core metrics**:

| Metric | Target (ideal) | Direction | Floor (score = 0) |
|--------|----------------|-----------|-------------------|
| Debt-to-Equity (%) | ≤ 70% | Lower is better | ≥ 300% |
| Return on Equity (%) | ≥ 15% | Higher is better | ≤ 0% (negative) |
| Revenue Growth YoY (%) | ≥ 10% | Higher is better | ≤ -20% |
| Revenue Growth 5yr CAGR (%) | ≥ 10% | Higher is better | ≤ -5% |
| Forward P/E | ≤ 20 | Lower is better | ≥ 60 |
| Profit Margin (%) | ≥ 20% | Higher is better | ≤ 0% (negative) |

Dividend-paying stocks are also scored on these **dividend metrics**:

| Metric | Target (ideal) | Direction | Floor (score = 0) |
|--------|----------------|-----------|-------------------|
| Payout Ratio (%) | ≤ 40% | Lower is better | ≥ 100% |
| Consecutive Years Paid | ≥ 10 | Higher is better | 0 |
| Consecutive Years Growth | ≥ 10 | Higher is better | 0 |
| 5yr Dividend Growth CAGR (%) | ≥ 6% (2× inflation) | Higher is better | ≤ 0% |

Growth stocks add this metric instead:

| Metric | Target (ideal) | Direction | Floor (score = 0) |
|--------|----------------|-----------|-------------------|
| Forward PEG | ≤ 1.0 | Lower is better | ≥ 3.0 |

#### Metric Weighting

**For dividend stocks:**
- **Consecutive Years Paid**: 2× weight
- **5yr Dividend Growth CAGR**: 2× weight
- All other metrics: 1× weight
- Total weights: 6 core metrics (1× each = 6) + 4 dividend metrics (2× + 1× + 1× + 2× = 6) = **12 total weight units**

**For growth/prospect stocks:**
- **Forward PEG**: 2× weight
- **Return on Equity**: 2× weight
- **Revenue Growth 5yr CAGR**: 2× weight
- All other metrics: 1× weight
- Total weights: 6 core metrics (1× + 2× + 1× + 2× + 1× + 1× = 8) + 1 growth metric (2×) = **10 total weight units**

#### Scoring Algorithm

For each metric, calculate a **metric score from 0.0 to 1.0** based on linear interpolation between the floor (0.0) and target (1.0):

**"Lower is better" metrics** (D/E, Forward P/E, Payout Ratio, FWD PEG):
```
metric_score = max(0, min(1, (floor - actual) / (floor - target)))
```
- At or below target → 1.0
- At or above floor → 0.0
- Between → linear interpolation

**"Higher is better" metrics** (ROE, Revenue Growth, Profit Margin, Dividend Growth, Consecutive Years):
```
metric_score = max(0, min(1, (actual - floor) / (target - floor)))
```
- At or above target → 1.0
- At or below floor → 0.0
- Between → linear interpolation

**Infrastructure score (0–10):**
```
weighted_sum = Σ (metric_score × weight) for each metric
max_weighted_sum = Σ (weight) for each metric
infrastructure_score = round(weighted_sum / max_weighted_sum * 10)
```

**If a metric is unavailable** (yfinance returns null): Exclude it from both the weighted sum and the max weighted sum. Score on available metrics only.

#### Hard Rules

- **LIQUIDITY FLOOR**: If `avg_daily_volume × stock_price < $1,000,000` → Infrastructure score = **0** regardless of all other metrics. The stock is too illiquid for IOWN to trade.
- **Metric floor at 0**: No metric can contribute a negative score. Extremely bad metrics (D/E of 500%, ROE of -50%) simply score 0.0 on that component.

#### Infrastructure Calibration Anchors

**Dividend 10 — QCOM**: D/E under 70%, ROE over 15%, double-digit 5yr revenue CAGR, double-digit YoY revenue growth, Forward P/E under 20, payout ratio under 40%, 10+ consecutive years paid, 10+ consecutive years of growth, 5yr dividend growth CAGR more than double inflation.

**Growth 10 — HRMY**: D/E under 70%, ROE over 15%, profit margin ~60%, double-digit 5yr revenue growth CAGR, double-digit YoY revenue growth, Forward PEG under 1, Forward P/E under 20.

---

## Dimension 2: AI Resilience (25% of overall)

Single score /10. Scored as two components: **AI Risk Protection (9 points)** and **AI Opportunity (1 point, tiebreaker)**.

AI Resilience primarily measures how immune this company's core business is to AI disruption. A company that is completely safe from AI disruption should score near the top — it is, by definition, maximally resilient. AI revenue contribution serves only as a tiebreaker to differentiate among companies with similar risk profiles.

### Part A: AI Risk Protection (0–9 points)

This is the core question: **Will AI hurt this company's earnings?** Claude Code must research what analysts, industry reports, and management are saying about AI's impact on the company's specific business lines. This is NOT a sector lookup — it requires company-specific analysis based on what analysts are actually saying.

| Points | AI Risk Level | Description |
|--------|---------------|-------------|
| 8–9 | **IMMUNE** | AI cannot replace what this company does. The business involves physical-world operations, deeply regulated processes, or essential infrastructure that AI structurally cannot displace. Analysts see zero substitution risk. AI may even increase demand for the company's products/services (e.g., AI data centers need more electricity, more semiconductors, more cooling). A company that IS AI infrastructure also scores here — you can't be disrupted by the thing you're building. |
| 6–7 | **PROTECTED** | Core business has meaningful defensive moats against AI disruption — regulatory requirements, switching costs, physical infrastructure, or proprietary data that AI can't easily replicate. Some business lines may face AI pressure but the core is defensible. Analysts are not concerned about AI displacement. |
| 3–5 | **EXPOSED** | AI creates real substitution risk for meaningful portions of the business. Some product lines or services could be partially replaced by AI tools. The company is adapting but the outcome is uncertain. Analysts have flagged AI as a risk factor. |
| 0–2 | **VULNERABLE** | AI directly threatens the core business model. Primary revenue streams face replacement or severe compression from AI tools that are already shipping or in development. The company has no clear defensive moat against AI substitution. Analysts are actively warning about AI disruption risk. |

**Evidence Claude Code must find:** Search for `"{Company Name}" AI disruption risk analyst` and `"{Company Name}" artificial intelligence impact earnings`. Look for specific analyst commentary, management discussion in earnings calls, and industry reports on AI's impact on this company's sector and business lines. The score must reflect what analysts and the market are actually saying — not Claude Code's own speculation.

### Part B: AI Opportunity (0–1 point, tiebreaker)

This is a single tiebreaker point that differentiates between two companies with identical risk profiles. It rewards companies that are actively generating revenue from AI.

| Points | AI Revenue Contribution |
|--------|------------------------|
| 1 | **Meaningful AI revenue.** The company generates quantifiable revenue from AI-related products, services, or infrastructure (any amount — from early-stage AI products shipping to AI being the entire business). Specific revenue figures or percentages must be cited. |
| 0 | **No AI revenue.** The company does not generate meaningful revenue from AI products or services. |

### AI Resilience Score

```
ai_resilience = ai_risk_protection + ai_opportunity
```

Max: 9 + 1 = **10**

### Labels

| Score | Label |
|-------|-------|
| 8–10 | LOW RISK |
| 5–7 | MODERATE |
| 1–4 | HIGH RISK |

---

## Dimension 3: Infinite Game (25% of overall)

Scored using a **3-2-2-2-1 weighted checklist** across five sub-dimensions derived from Simon Sinek's *The Infinite Game*. Max 10 points. The sub-dimension scores reported in the JSON are for display/detail purposes — the overall Infinite Game score (which feeds into the composite) is the weighted sum described below.

### Voice and Lens

Claude Code must score this dimension **as Simon Sinek would**. This means:

- Sinek evaluates companies on whether they are playing to **keep playing** (infinite) or playing to **win this quarter** (finite). The question is never "is this company successful?" — it's "is this company built to endure?"
- Sinek values **consistency of purpose over time** above all else. A company that has held the same Just Cause through multiple market cycles, leadership transitions, and crises is the gold standard.
- Sinek is deeply skeptical of companies that optimize for quarterly earnings, pursue growth through financial engineering (debt-funded buybacks, serial acquisitions for revenue), or change strategy every 2-3 years chasing the next trend.
- Sinek distinguishes between a **Just Cause** (a vision of a future state so appealing that people will sacrifice to advance it) and a **mission statement** (a corporate platitude). Most companies have missions. Very few have a Just Cause.
- Sinek believes **Courage to Lead** is where infinite game thinking gets tested — anyone can articulate a Just Cause when times are good. The test is whether leadership holds to it when it's costly: investing during downturns, walking away from profitable but misaligned businesses, choosing long-term capability over short-term earnings.
- Sinek treats **Trusting Teams** as the organizational foundation — without psychological safety, people protect themselves rather than advance the cause. He looks for evidence that employees are empowered to take risks, admit mistakes, and challenge leadership.
- **Worthy Rivals** in Sinek's framework are not competitors to beat — they are companies whose strengths reveal your own weaknesses. He looks for whether the company's competitive language is about "improving" or "winning." Companies that obsess over market share and competitor destruction are playing a finite game.
- **Existential Flexibility** is the willingness to make a dramatic strategic shift — even abandoning a profitable business — in service of the Just Cause. Sinek's canonical examples: Apple abandoning the Macintosh platform for the iPhone; Fujifilm pivoting from film to healthcare and materials while Kodak clung to film.

### Sub-Dimensions (weighted 3-2-2-2-1)

#### 1. Just Cause (max 3 points) — MOST IMPORTANT

Sinek defines a Just Cause as: resilient (it endures beyond any single product or leader), inclusive (it invites others to contribute), service-oriented (it benefits others, not just the company), idealistic (it describes a future state that does not yet exist), and big (it is so bold it can never be fully achieved).

| Points | Description |
|--------|-------------|
| 0 | **No Just Cause evident.** The company exists to make money, grow revenue, or "maximize shareholder value." There is no articulated vision of a better future. This is a finite player. |
| 1 | **Cause exists but is shallow.** The company has a purpose statement but it reads as marketing — interchangeable with any peer. Leadership doesn't reference it in strategic decisions. It doesn't shape behavior. |
| 2 | **Genuine cause, partially lived.** The company has a distinctive purpose that connects its work to something bigger. Leadership references it. Some strategic decisions can be traced back to it. But it hasn't been tested through crisis or multi-decade consistency. |
| 3 | **Just Cause is the competitive advantage.** The purpose has been validated by decades of consistent execution. It survived leadership transitions, market crises, and industry disruption. Strategic decisions clearly trace back to it. People join and stay because of it. Sinek would cite this company as an example. (e.g., NVDA: "accelerate computing" validated by 17 years of CUDA investment before the AI boom) |

#### 2. Courage to Lead (max 2 points)

Sinek says courage is not the absence of fear — it's acting in service of the Just Cause even when the cost is real and immediate. He looks for leaders who sacrifice short-term performance for long-term capability.

| Points | Description |
|--------|-------------|
| 0 | **No evidence of courageous decisions.** Leadership optimizes for quarterly earnings. No examples of sacrificing near-term results for long-term capability. Or worse — leadership makes decisions that protect their own position at the company's expense. |
| 1 | **Some courageous decisions.** At least one example of leadership choosing long-term investment over short-term earnings, walking away from revenue that conflicted with the company's direction, or taking a principled stance that cost money. |
| 2 | **Pattern of courage.** Multiple examples of leadership making costly long-term bets: investing heavily in R&D during downturns, exiting profitable but misaligned businesses, making capital allocation decisions that prioritize future capability over current earnings. The company has a track record of choosing right over easy. |

#### 3. Trusting Teams (max 2 points)

Sinek's "Circle of Safety" — do people inside the organization feel safe enough to be vulnerable, take risks, and admit mistakes? Or do they spend energy protecting themselves from internal politics?

| Points | Description |
|--------|-------------|
| 0 | **Low-trust environment.** Evidence of frequent layoffs, high turnover, fear-based management, or organizational instability. Employees describe a political or cutthroat culture. Leadership changes are disruptive. |
| 1 | **Adequate trust.** Stable organization without major cultural red flags. Employees generally stay, leadership is consistent, but there's no evidence of exceptional trust or empowerment. Average for the industry. |
| 2 | **High-trust organization.** Evidence of employee empowerment, long average tenure, low voluntary turnover, leadership continuity, or cultural practices that create psychological safety. Employees describe feeling valued and trusted. People cite the culture as a reason they stay. |

#### 4. Existential Flexibility (max 2 points)

The willingness to blow up your own business model — to abandon what's working today in service of what the Just Cause demands tomorrow. Sinek's test: has the company ever made a strategic pivot that was painful in the short term but essential for long-term relevance?

| Points | Description |
|--------|-------------|
| 0 | **Rigid.** The company clings to its legacy business model even as the world changes around it. No evidence of strategic adaptation. Or the company is too young/small to have faced this test. |
| 1 | **Some flexibility.** The company has evolved its business model over time — entering adjacent markets, adopting new technologies, or restructuring in response to industry shifts. The changes were incremental, not transformative. |
| 2 | **Transformative flexibility.** The company has fundamentally reinvented itself at least once — abandoning a core business, entering an entirely new market, or making a bet that redefined the company. The pivot was driven by the Just Cause, not desperation. (e.g., NVDA: gaming GPUs → crypto → AI; Apple: Mac → iPod → iPhone) |

#### 5. Worthy Rivals (max 1 point) — LEAST IMPORTANT

Sinek's worthy rival concept: other players whose strengths reveal your weaknesses and push you to improve. It's a mindset question — does the company compete to learn or compete to destroy?

| Points | Description |
|--------|-------------|
| 0 | **Finite competitive mindset.** The company's language is about "beating" competitors, "winning" market share, or "crushing" rivals. Competitive strategy is about others' weaknesses, not self-improvement. Or the company is a monopoly with no competitive awareness. |
| 1 | **Infinite competitive mindset.** The company acknowledges competitors' strengths, uses competitive pressure to improve its own offerings, and frames competition as motivation to get better rather than a war to win. Evidence: management commentary that references learning from rivals, product improvements inspired by competitive dynamics, or explicit acknowledgment of worthy competitors. |

### Infinite Game Score

```
infinite_game_overall = just_cause + courage_to_lead + trusting_teams + existential_flexibility + worthy_rivals
```

Max: 3 + 2 + 2 + 2 + 1 = **10**

### Labels

| Score | Label |
|-------|-------|
| 8–10 | **INFINITE** |
| 5–7 | **MIXED** |
| 1–4 | **FINITE** |

### Sub-Dimension Scores in JSON

The report JSON still includes individual sub-dimension scores for display purposes. To convert from the weighted points above to the /10 display scores:

- **Just Cause**: 0 pts → 1/10, 1 pt → 4/10, 2 pts → 7/10, 3 pts → 10/10
- **Courage to Lead**: 0 pts → 2/10, 1 pt → 6/10, 2 pts → 10/10
- **Trusting Teams**: 0 pts → 2/10, 1 pt → 6/10, 2 pts → 10/10
- **Existential Flexibility**: 0 pts → 2/10, 1 pt → 6/10, 2 pts → 10/10
- **Worthy Rivals**: 0 pts → 3/10, 1 pt → 10/10

These display scores are for the report only — they do not feed into the overall composite. Only the weighted sum (the Infinite Game overall /10) feeds into the composite.

---

## Faith Alignment — Display Only (0% weight)

The Inspire Impact Score (-100 to +100) is displayed on the report for reference. It does NOT factor into the overall score.

**Source**: Always from `data/inspire_insight_scores.csv`. Never web searched. Never estimated.

**Labels** (display only):
- Score > 25: **ALIGNED**
- Score -25 to 25: **MIXED**
- Score < -25: **MISALIGNED**

Include `negative_attributions` and `positive_attributions` from the CSV in the report JSON.

---

## Dimensions NOT Scored

The following dimensions existed in previous versions of SCREENING.md but are **removed**. Do not score, display, or reference them:

- Social Arbitrage (Camillo lens)
- Moat Strength
- Erosion Protection
- Income Quality / Dividend Safety as a standalone dimension (dividend metrics now live inside Infrastructure)

---

## Quality Standards

1. **Every score must cite specific evidence.** "Strong balance sheet" is not evidence. "$62.6B cash against $11.4B debt with 101% ROE" is evidence.
2. **Infrastructure scores are calculated, not assigned.** Run the metric-to-score algorithm. Show your work by including all metrics in the JSON.
3. **Innovation scores are checklist-driven.** Score each of the 5 evidence items independently, then sum. Do not assign a holistic score — add up the points.
4. **Inspiration scores start with the mission floor.** Visit the company's website, evaluate the mission quality (0-4), then score the three evidence adds (0-2 each). Sum them.
5. **AI Resilience is split 70/30.** Score AI Risk Protection (0-7) based on analyst research, then AI Opportunity (0-3) based on actual AI revenue. Sum them.
6. **Infinite Game is scored as Simon Sinek would.** Use the 3-2-2-2-1 weighted checklist. Claude Code must adopt Sinek's lens — the question is always "is this company built to endure?" not "is this company successful?"
7. **Use the full range.** A score of 3 is appropriate for a struggling company. A score of 10 is rare and should be earned. The median overall score across the universe should be approximately 5.
8. **Investment thesis is two paragraphs.** First: bull case with specific data. Second: bear case with specific risks and quantification.
9. **Key catalysts and risks are specific and actionable.** Not "market downturn" but "secular decline in core cereal category as consumers shift to fresh/less-processed alternatives."

---

## Example: Infrastructure Calculation for QCOM (Dividend)

Hypothetical metrics:
- D/E: 60% → target ≤70%, floor 300% → score = (300-60)/(300-70) = 1.04 → capped at **1.0**
- ROE: 40% → target ≥15%, floor 0% → score = (40-0)/(15-0) = 2.67 → capped at **1.0**
- Rev Growth YoY: 15% → target ≥10%, floor -20% → score = (15-(-20))/(10-(-20)) = 1.17 → capped at **1.0**
- Rev Growth 5yr CAGR: 12% → target ≥10%, floor -5% → score = (12-(-5))/(10-(-5)) = 1.13 → capped at **1.0**
- Forward P/E: 15 → target ≤20, floor 60 → score = (60-15)/(60-20) = 1.125 → capped at **1.0**
- Profit Margin: 25% → target ≥20%, floor 0% → score = (25-0)/(20-0) = 1.25 → capped at **1.0**
- Payout Ratio: 35% → target ≤40%, floor 100% → score = (100-35)/(100-40) = 1.08 → capped at **1.0** (1× weight)
- Consec Years Paid: 22 → target ≥10, floor 0 → score = (22-0)/(10-0) = 2.2 → capped at **1.0** (2× weight)
- Consec Years Growth: 15 → target ≥10, floor 0 → score = (15-0)/(10-0) = 1.5 → capped at **1.0** (1× weight)
- 5yr Div Growth CAGR: 8% → target ≥6%, floor 0% → score = (8-0)/(6-0) = 1.33 → capped at **1.0** (2× weight)

Weighted sum: (1×1.0) + (1×1.0) + (1×1.0) + (1×1.0) + (1×1.0) + (1×1.0) + (1×1.0) + (2×1.0) + (1×1.0) + (2×1.0) = **12.0**
Max weighted sum: 1+1+1+1+1+1+1+2+1+2 = **12**
Infrastructure score: 12.0 / 12 × 10 = **10**

## Example: Infrastructure Calculation for a Weak Stock

Hypothetical metrics:
- D/E: 200% → score = (300-200)/(300-70) = 0.435 → **0.44**
- ROE: 5% → score = (5-0)/(15-0) = 0.333 → **0.33**
- Rev Growth YoY: -5% → score = (-5-(-20))/(10-(-20)) = 0.5 → **0.50**
- Rev Growth 5yr CAGR: 0% → score = (0-(-5))/(10-(-5)) = 0.333 → **0.33**
- Forward P/E: 40 → score = (60-40)/(60-20) = 0.5 → **0.50**
- Profit Margin: 5% → score = (5-0)/(20-0) = 0.25 → **0.25**
- Forward PEG: 2.0 → score = (3-2)/(3-1) = 0.5 → **0.50** (2× weight)

Weighted sum: (1×0.44) + (2×0.33) + (1×0.50) + (2×0.33) + (1×0.50) + (1×0.25) + (2×0.50) = **4.01**
Max weighted sum: 1+2+1+2+1+1+2 = **10**
Infrastructure score: 4.01 / 10 × 10 = **4** (rounded)

---

## JSON Schema Changes

The report JSON schema remains the same as defined in CLAUDE.md with these modifications:

1. **No `social_arbitrage` field** — removed entirely
2. **No `moat_strength` field** — removed entirely  
3. **No `erosion_protection` field** — removed entirely
4. **`income_quality.dividend_safety`** — removed as a standalone scored dimension. Dividend metrics are captured inside `excellence_evaluation.infrastructure.metrics.dividend` and factor into the Infrastructure sub-score.
5. **`faith_alignment`** — remains in the JSON for display purposes but carries 0% weight
6. **`overall_score`** — calculated using the new 50/25/25 formula only

The `income_quality` key can be removed from the JSON schema entirely, OR retained as `null` for backwards compatibility with the HTML template. Recommend removing it and updating the template.

---

## Migration Notes

When re-screening existing stocks with this rubric:

1. Infrastructure scores will change significantly — they are now calculated mechanically rather than assigned qualitatively
2. Overall scores will shift because weights changed from 5×20% to 50/25/25
3. Some stocks currently in HOLD territory may move to WATCH or BUY as the scoring becomes more differentiated
4. The score distribution should widen — expect more separation between strong and weak names
5. Sleeve assignments for current holdings will now be forced from portfolios.json, fixing the category mismatches
