# IOWN Opportunity Finder — Daily Task

You are running the IOWN Opportunity Finder at `/home/user/Stock-Screener`. Your job is to identify compelling investment opportunities by connecting macro events, supply chain dynamics, and sector trends to stocks we've already screened.

**Do NOT force opportunities.** Only create one when there's a genuinely compelling catalyst backed by evidence. Some days there will be nothing. That's fine.

## Step 1: Scan for Catalysts

Do 3-5 web searches for current macro events:

1. `major geopolitical events supply chain disruption 2026`
2. `AI infrastructure spending earnings surprises 2026`
3. `commodity supply shock shortage 2026`
4. `technology sector rotation institutional money flow 2026`
5. `federal reserve policy impact sectors 2026`

Look for events that create **asymmetric opportunities** — situations where the market hasn't fully priced in the second or third-order effects of a catalyst.

## Step 2: Match to Screened Stocks

Check which stocks in `reports/` could benefit from any catalyst you find. Only consider stocks we already have IOWN reports for.

```bash
ls reports/*.json | wc -l  # See how many stocks are available
```

## Step 3: Evaluate Opportunity Quality

Only create an opportunity if it meets ALL of these criteria:

1. **Clear catalyst** — a specific, identifiable event or trend (not vague "AI is growing")
2. **Logical connection** — the link between the catalyst and the stock is defensible and specific
3. **Timing relevance** — the opportunity is actionable now, not 5 years from now
4. **Not already obvious** — if everyone on CNBC is talking about it, it's too late

### Opportunity Patterns to Look For

| Pattern | Description | Example |
|---------|-------------|---------|
| **Supply Chain / Picks & Shovels** | X is spending big → who supplies X? | NVDA investing in optical interconnects → CRDO, MRVL |
| **Supply Shock / Scarcity** | Supply of Y disrupted → who fills the gap? | Iran war disrupts ammonia → NTR |
| **Secular Trend Acceleration** | Long-term trend hitting an inflection point | AI + quantum → cybersecurity demand → FTNT |

### Conviction Tiers

- **High Conviction**: Multiple data points confirm the thesis. Clear catalyst with specific timeline. Institutional money already moving.
- **On Our Radar**: Interesting thesis but needs more confirmation. Early signal, worth watching.

## Step 4: Write the Opportunity JSON

If you find something compelling, write it to `opportunities/{id}.json`:

```json
{
  "id": "descriptive-slug",
  "title": "Short Descriptive Title",
  "pattern": "Supply Chain|Supply Shock|Secular Trend",
  "conviction": "High Conviction|On Our Radar",
  "status": "active",
  "date_identified": "YYYY-MM-DD",
  "catalyst": "2-3 sentences describing the specific event or trend that creates the opportunity.",
  "thesis": "2-3 sentences explaining WHY this catalyst benefits specific stocks. Connect the dots — don't just say 'AI is growing', explain the second-order effect.",
  "tickers": ["TICK1", "TICK2"],
  "ticker_rationale": {
    "TICK1": "1-2 sentences explaining why THIS specific stock benefits. Cite specific data — market share, revenue exposure, competitive position.",
    "TICK2": "Same for this stock."
  },
  "risks": [
    "Specific risk that could invalidate the thesis",
    "Another specific risk with scenario"
  ],
  "timeframe": "3-6 months|6-12 months|12-24 months|12-36 months",
  "sources": [
    "Specific source with date",
    "Another source"
  ]
}
```

**Rules:**
- Tickers MUST have existing reports in `reports/`. Check before including.
- IDs are lowercase kebab-case slugs
- Only create opportunities for events that have ALREADY happened or are clearly underway — not predictions
- Max 2-3 opportunities per run. Quality over quantity.
- If no compelling opportunity exists today, write nothing. That's the right answer.

## Step 5: Review Existing Opportunities

Check if any existing opportunities should be marked as expired:

```bash
ls opportunities/*.json
```

For each existing opportunity, evaluate:
- Has the catalyst played out? (stock already moved significantly)
- Has the thesis been invalidated? (ceasefire, policy reversal, etc.)
- Is the timeframe expired?

If so, update the `"status"` field to `"expired"`.

## Step 6: Commit, Push, Rebuild, and Deploy

```bash
git add opportunities/*.json
git diff --cached --quiet || git commit -m "Opportunity finder: [brief description of changes]"
git push -u origin HEAD

# Rebuild the site so opportunities appear on the live screener
python3 main.py

# Deploy ONLY the updated index.html (opportunities tab) to gh-pages
# This is fast — don't redeploy all report files
source .env && export GITHUB_PUSH_TOKEN
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
"
```

## Important Notes

- **Quality over quantity** — one great opportunity per week is better than five mediocre ones
- **Be specific** — "AI is growing" is not a thesis. "NVIDIA's Rubin platform requires 3.2T optical links, creating $5B TAM for AEC suppliers" is a thesis
- **Check your work** — verify that tickers you mention have reports in `reports/`
- **Don't duplicate** — check existing opportunities before creating a new one on the same theme
- **Expire old ones** — opportunities that have played out or been invalidated should be marked expired
