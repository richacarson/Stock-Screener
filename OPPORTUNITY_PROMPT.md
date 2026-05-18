# IOWN Opportunity Finder — Daily Task

You are running the IOWN Opportunity Finder at `/home/user/Stock-Screener`. Your job is to identify compelling investment opportunities and write them as **full research reports with verified sources**.

**Do NOT force opportunities.** Only create one when there's a genuinely compelling, evidence-backed catalyst. Some days there will be nothing. That's the right answer.

## Step 1 — Establish today's macro context (cheap)

Before searching, write a short scratch note to `/tmp/today_brief.md`:
- Today's date and trading day status
- 3–5 macro headlines from the last 24h (use `web_search` with queries you choose adaptively based on what's actually moving — **do not use the same hard-coded queries every day**)
- Any FOMC/ECB/BOJ events, earnings of note, geopolitical shifts, commodity prints

This gives you a focused universe for Step 2 instead of cold searches.

## Step 2 — Hunt for asymmetric setups

Re-read `/tmp/today_brief.md`. Ask: *which of these creates a second- or third-order effect the market is mispricing?* Examples:
- Capex commitment by hyperscaler X → who supplies the pick-and-shovel?
- Geopolitical shock to commodity Y → who has spare capacity?
- Regulatory shift in industry Z → who's structurally advantaged?

If nothing meets this bar, **stop here and exit cleanly**. Don't write a JSON. Quality > quantity.

## Step 3 — Match to screened universe

For any candidate thesis, identify 1–3 tickers that benefit. **Each ticker MUST have a report in `reports/`.** Then:

```bash
cat reports/{TICKER}.json
```

Pull at least 3 specific data points (forward P/E, ROE, margin, growth rate, backlog, market share, AI resilience score, etc.) that you'll weave into the thesis. **Do not write the report without reading these.**

## Step 4 — Deep research with citations

This is the expensive step. Use `web_search` to gather primary-source evidence:
- Company press releases / 8-Ks / earnings call transcripts
- Industry trade publications (Utility Dive, SemiAnalysis, Stratechery, etc.)
- Government data (EIA, USDA, BLS, FRED) where applicable
- Analyst notes from Tier-1 banks when publicly summarized

**Every factual claim in the report must have a citation.** Numbers (revenue, backlog, prices, multiples) must come from a source you can link, or from the screener report in `reports/`.

Cross-check any price/EPS/multiple you cite against the screener report or a fresh API call. **If the numbers don't agree, don't ship the opportunity** — investigate.

## Step 5 — Write the opportunity JSON

Schema (write to `opportunities/{id}.json`):

```json
{
  "id": "descriptive-slug",
  "title": "Short Descriptive Title (≤80 chars)",
  "summary": "One-sentence elevator pitch. What's the trade in plain English?",
  "pattern": "Supply Chain | Supply Shock | Secular Trend | Regulatory | Cyclical",
  "conviction": "High Conviction | On Our Radar",
  "status": "active",
  "date_identified": "YYYY-MM-DD",
  "timeframe": "3-6 months | 6-12 months | 12-24 months | 12-36 months",
  "tickers": ["TICK1", "TICK2"],
  "in_portfolio": true,
  "catalyst": "2-3 sentences: the specific event/trend that creates the opportunity. Reference a date.",
  "thesis": "2-3 sentences: the second-order effect. Why does the catalyst translate to these specific tickers?",
  "body_md": "Full research report in markdown — 800–1500 words. Use ## headings. Embed inline citations like [1], [2] that map to the sources array. Include sections: Setup, Why Now, Company-Specific Edge (per ticker), Numbers That Matter, Bear Case, Conclusion. Use tables for peer comparisons when useful.",
  "ticker_rationale": {
    "TICK1": "1-2 sentences with at least one specific number from the screener report or your research.",
    "TICK2": "Same."
  },
  "key_metrics": {
    "TICK1": {"Fwd P/E": 18.2, "ROE": "22%", "Backlog": "100 GW", "FY26 EPS Growth": "55%"},
    "TICK2": {"Fwd P/E": 14.1, "Div Yield": "3.2%", "Payout Ratio": "45%"}
  },
  "risks": [
    "Specific risk with a scenario, not 'macro risk'",
    "Another specific risk"
  ],
  "invalidation": [
    "Specific price level, earnings number, or event that would close this trade",
    "Another concrete invalidation trigger"
  ],
  "sources": [
    {"id": 1, "url": "https://...", "title": "Article or filing title", "publisher": "WSJ | SEC | Company IR | Utility Dive | etc.", "date": "2026-05-12", "accessed": "2026-05-18"},
    {"id": 2, "url": "https://...", "title": "...", "publisher": "...", "date": "..."}
  ]
}
```

**Rules:**
- `body_md` is **mandatory** for new opportunities. Don't skip it.
- `sources` are **objects**, not strings. Every source needs a real URL you actually opened.
- `invalidation` is **mandatory** — at least 2 concrete triggers.
- Tickers MUST exist in `reports/`. Check first.
- IDs are lowercase kebab-case.
- Only document events that have happened or are clearly underway — not predictions.
- Max 2 new opportunities per run. Usually zero is correct.

## Step 6 — Expire old opportunities

For each active opportunity, evaluate:
- Has any invalidation trigger fired?
- Has 30+ days passed without the thesis advancing?
- Has the timeframe expired?

If yes, set `status: "expired"`.

## Step 7 — Commit, Push, Rebuild, and Deploy

```bash
git add opportunities/*.json
git diff --cached --quiet || git commit -m "Opportunity finder: [brief description of changes]"
git push -u origin HEAD

# Rebuild the site so opportunities appear on the live screener
python3 main.py

# Deploy ONLY the updated index.html (opportunities tab) to gh-pages
# This is fast — don't redeploy all report files
# Load token from environment or .env file
if [ -z "${GITHUB_PUSH_TOKEN:-}" ] && [ -f .env ]; then source .env && export GITHUB_PUSH_TOKEN; fi
python3 -c "
import os, json, base64, time
from urllib.request import Request, urlopen
from pathlib import Path

TOKEN = os.environ['GITHUB_PUSH_TOKEN']
API = 'https://api.github.com/repos/richacarson/Stock-Screener'

def api(method, endpoint, data=None):
    url = API + endpoint
    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, method=method)
    req.add_header('Authorization', 'token ' + TOKEN)
    req.add_header('Content-Type', 'application/json')
    for attempt in range(5):
        try:
            return json.loads(urlopen(req, timeout=60).read())
        except Exception as e:
            if attempt < 4: time.sleep(2 ** (attempt + 1))
            else: raise

# Only deploy changed files — index.html has the opportunities tab
tree_items = []
for fpath in ['output/index.html', 'output/manifest.json']:
    p = Path(fpath)
    rel = str(p.relative_to('output'))
    content = base64.b64encode(p.read_bytes()).decode()
    blob = api('POST', '/git/blobs', {'content': content, 'encoding': 'base64'})
    tree_items.append({'path': rel, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})

parent_sha = api('GET', '/git/ref/heads/gh-pages')['object']['sha']
parent_tree = api('GET', '/git/commits/' + parent_sha)['tree']['sha']
tree = api('POST', '/git/trees', {'base_tree': parent_tree, 'tree': tree_items})
commit = api('POST', '/git/commits', {'message': 'Deploy: update opportunities', 'tree': tree['sha'], 'parents': [parent_sha]})
api('PATCH', '/git/refs/heads/gh-pages', {'sha': commit['sha'], 'force': True})
print('Deployed opportunities to gh-pages!')

# Also deploy to Dashboard repo (richacarson/Dashboard)
DASH_API = 'https://api.github.com/repos/richacarson/Dashboard'

def dash_api(method, endpoint, data=None):
    url = DASH_API + endpoint
    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, method=method)
    req.add_header('Authorization', 'token ' + TOKEN)
    req.add_header('Content-Type', 'application/json')
    for attempt in range(5):
        try:
            return json.loads(urlopen(req, timeout=60).read())
        except Exception as e:
            if attempt < 4: time.sleep(2 ** (attempt + 1))
            else: raise

dash_items = []
opp_dir = Path('opportunities')
opps_manifest = []
for f in sorted(opp_dir.glob('*.json')):
    content = base64.b64encode(f.read_bytes()).decode()
    blob = dash_api('POST', '/git/blobs', {'content': content, 'encoding': 'base64'})
    dash_items.append({'path': f'public/opportunities/{f.name}', 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
    d = json.load(open(f))
    opps_manifest.append(d.get('id', f.stem))

manifest_blob = dash_api('POST', '/git/blobs', {'content': base64.b64encode(json.dumps(opps_manifest, indent=2).encode()).decode(), 'encoding': 'base64'})
dash_items.append({'path': 'public/opportunities/manifest.json', 'mode': '100644', 'type': 'blob', 'sha': manifest_blob['sha']})

dash_ref = dash_api('GET', '/git/ref/heads/main')
dash_parent = dash_ref['object']['sha']
dash_parent_tree = dash_api('GET', f'/git/commits/{dash_parent}')['tree']['sha']
dash_tree = dash_api('POST', '/git/trees', {'base_tree': dash_parent_tree, 'tree': dash_items})
dash_commit = dash_api('POST', '/git/commits', {'message': 'Update opportunities from Stock-Screener', 'tree': dash_tree['sha'], 'parents': [dash_parent]})
dash_api('PATCH', '/git/refs/heads/main', {'sha': dash_commit['sha']})
print('Deployed opportunities to Dashboard!')
"
```

## Quality bar — non-negotiable

- "AI is growing" is not a thesis. "Hyperscalers committed $X in 2026 capex, sold-out gas turbine slots at Y company through 2030 per [filing]" is a thesis.
- Every number traceable to a source.
- Every URL opened, not invented.
- If you can't find primary sources for a claim, drop the claim.
- If you can't write 800+ words of substance, the thesis isn't ready — skip it.
