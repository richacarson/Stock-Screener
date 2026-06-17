# IOWN Opportunity Finder — Daily Task

You are running the IOWN Opportunity Finder at `/home/user/Stock-Screener`. Your job is to maintain a high-quality, actively-managed set of investment opportunities — not to file as many as possible.

**Quality > quantity, but visibility > silence.** Most days "no new High Conviction opp today" is acceptable. But the team needs to see what you're considering. Three conviction tiers:

- **High Conviction** — passes ALL criteria in Step 5. Goes into the active manifest with full trade construction. The team can act on these.
- **On Our Radar** — passes most criteria but missing one (e.g., trade construction is approximate, or only 1 primary source so far). Sits in the manifest at lower position size guidance. Team monitors these.
- **Stalking** — interesting catalyst with at least one credible source, but doesn't yet justify the On Our Radar bar. No trade construction required. Sits in a separate `stalking.json` file for team visibility. Re-evaluated daily; can graduate to higher tiers as evidence accumulates.

**Minimum cadence rule.** If no new High Conviction or On Our Radar opp has been filed in the last 14 days, you MUST surface at least 2 Stalking candidates this run — even if they only barely clear the Stalking bar. Show your work; don't go silent.

The routine maintains these files under `opportunities/`:
- `manifest.json` — list of ACTIVE opp IDs (regenerated in Step 8)
- `<id>.json` — one file per active opp (High Conviction + On Our Radar)
- `ledger.json` — closed opps, append-only history
- `signals.json` — daily insider / congressional / institutional signals
- `stalking.json` — Stalking-tier candidates the team is watching
- `team_feedback.json` — team notes (read-only — populated by humans)
- `committee_lookup.json` — cached Congress → committee map (quarterly refresh)
- `fund_cik_lookup.json` — cached SEC CIK per watched fund (quarterly refresh)

The Dashboard reads all of these from its `public/opportunities/` folder (synced at the end of this prompt).

---

## FIRST-RUN / RETROFIT POLICY (READ THIS FIRST)

The first time this updated prompt runs:
- **Do NOT retrofit existing opportunities** with new schema fields (`counter_thesis`, `trade_construction`, `catalyst_calendar`, `in_portfolio_status`). Existing opps keep their current shape.
- Apply the new schema **only to opportunities you open going forward**, or to existing opps you would have updated anyway.
- If `ledger.json` does not exist, create it as `[]`.
- If `signals.json` does not exist, create it from today's scrape.
- If `stalking.json` does not exist, create it as `[]`.
- Never fabricate entry / target / stop prices. Missing data stays missing.
- For housekeeping: only close existing opps if their invalidation criteria are clearly triggered. When in doubt, leave open.

---

## Step 0: Sync from prior runs

The screening routine runs on `claude/...` branches. Pull any opportunity files from recent screening branches that haven't reached main yet, so we don't accidentally orphan them.

```bash
git fetch origin

python3 -c "
import subprocess, os

result = subprocess.run(['git', 'branch', '-r'], capture_output=True, text=True)
screening_branches = [b.strip() for b in result.stdout.splitlines()
                      if 'daily-screening' in b and b.strip().startswith('origin/')]
opp_branches = [b.strip() for b in result.stdout.splitlines()
                if 'opportunity' in b.lower() and b.strip().startswith('origin/')]

for branch in sorted(set(screening_branches + opp_branches)):
    diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD', branch, '--', 'opportunities/', 'reports/'],
                          capture_output=True, text=True)
    new_files = [f for f in diff.stdout.splitlines()
                 if (f.startswith('opportunities/') or f.startswith('reports/')) and f.endswith('.json')]
    truly_new = [f for f in new_files if not os.path.exists(f)]
    if truly_new:
        print(f'{branch}: pulling {len(truly_new)} new files')
        subprocess.run(['git', 'checkout', branch, '--'] + truly_new)
"

git add reports/*.json opportunities/*.json 2>/dev/null
git diff --cached --quiet || git commit -m "Sync files from prior scheduled runs"
```

---

## Step 1: Read State

```bash
python3 -c "
import json, os
from pathlib import Path

OPP_DIR = Path('opportunities')
SUPPORT = {'manifest.json', 'ledger.json', 'signals.json',
           'committee_lookup.json', 'fund_cik_lookup.json',
           'team_feedback.json', 'stalking.json'}

# Active opps (enumerate from filesystem since manifest.json is regenerated)
active_files = sorted([f for f in os.listdir(OPP_DIR)
                       if f.endswith('.json') and f not in SUPPORT])
print(f'Active opportunities: {len(active_files)}')

# Ledger
ledger = json.load(open(OPP_DIR / 'ledger.json')) if (OPP_DIR / 'ledger.json').exists() else []
print(f'Closed opportunities in ledger: {len(ledger)}')

# Stalking
stalking = json.load(open(OPP_DIR / 'stalking.json')) if (OPP_DIR / 'stalking.json').exists() else []
print(f'Stalking-tier candidates: {len(stalking)}')

# Team feedback
if (OPP_DIR / 'team_feedback.json').exists():
    fb = json.load(open(OPP_DIR / 'team_feedback.json'))
    if fb:
        print(f'\\nRecent team feedback ({len(fb[-3:])} entries):')
        for entry in fb[-3:]:
            print(f'  {entry.get(\"date\",\"\")}: {entry.get(\"feedback\",\"\")}')

# Ledger stats by pattern — flag weak performers
if ledger:
    stats = {}
    for c in ledger:
        p = c.get('pattern','?')
        if p not in stats: stats[p] = {'n': 0, 'wins': 0, 'sum': 0}
        stats[p]['n'] += 1
        if (c.get('return_pct') or 0) > 0: stats[p]['wins'] += 1
        stats[p]['sum'] += (c.get('return_pct') or 0)
    print(f'\\nLedger by pattern:')
    for p, s in sorted(stats.items(), key=lambda x: -x[1]['n']):
        win_rate = s['wins'] / s['n'] * 100 if s['n'] else 0
        avg = s['sum'] / s['n'] if s['n'] else 0
        flag = ' (WEAK — raise bar)' if win_rate < 40 and s['n'] >= 3 else ''
        print(f'  {p}: n={s[\"n\"]}, win {win_rate:.0f}%, avg {avg:+.1f}%{flag}')
"
```

Note any pattern flagged WEAK — those require 3 primary sources instead of 2 (High Conviction) and a paragraph explaining why this case differs from the losing precedents.

---

## Step 2: Daily Housekeeping — DO THIS BEFORE OPENING ANY NEW OPPORTUNITY

For each active opportunity:

1. **Refresh prices** for each ticker.
2. **Stop check** — if `trade_construction.stop_loss` exists and is breached on a closing basis → status `"Stopped Out"`, write a 2-sentence post-mortem, delete the opp file, append to `ledger.json`.
3. **Invalidation check** — review each `invalidation` criterion. If triggered → `"Thesis Broken"`, same close flow.
4. **Target check** — if `trade_construction.target_12mo` is hit → `"Target Hit"`, same flow.
5. **Refresh key_metrics** from the latest screener report. If `recommendation` changed (BUY → HOLD, etc.), add a one-line `metrics_note` to the opp.

Then **age-out radar items**: any `On Our Radar` opp older than 30 days must either be upgraded to `"High Conviction"` (with a one-paragraph reason) or downgraded to `"Expired"` and moved to the ledger.

Then **age-out stalking items**: any `Stalking` entry older than 45 days must either be promoted to `On Our Radar` (with reason) or removed from `stalking.json` (with a one-line note in `team_feedback.json` explaining why).

When appending to `ledger.json`:

```json
{
  "id": "iran-ammonia-disruption",
  "title": "Iran Ammonia Supply Shock",
  "opened": "2026-04-01",
  "closed": "2026-05-28",
  "days_held": 57,
  "pattern": "Supply Shock",
  "theme": "Geopolitics/Chemicals",
  "tickers": ["NTR"],
  "entry_price_avg": 65.20,
  "exit_price_avg": 71.80,
  "return_pct": 10.1,
  "close_reason": "Target hit — NTR reached $70 in 8 weeks",
  "what_worked": "Iran-supply outage persisted longer than market expected.",
  "what_didnt": "Entry too small — only sized 1%, missed full upside.",
  "would_have_done": "If we'd watched CRU ammonia index daily, we'd have added at $62."
}
```

If `entry_price_avg` was never recorded, approximate using the closing price on `opened` and note that in `what_didnt`.

---

## Step 3: Rebuild `signals.json` — Free Public Data Only

**SEC EDGAR etiquette:** always set the User-Agent header to:
```
User-Agent: Paradiem Research carson.rich@paradiem.org
```
For openinsider.com, a generic `User-Agent: Paradiem Research bot` is fine. Throttle to ≤1 req/sec per host.

### 3a. Insider cluster buys (DAILY)

Source: `http://openinsider.com/insider-cluster-buys` (free HTML scrape — aggregates SEC Form 4).

Keep rows where ALL hold:
- ≥2 insiders
- Total purchase value ≥ $100,000
- Span ≤ 30 days
- Insider role includes CEO, CFO, COO, President, or Director

For each surviving ticker:
- Look up the current screener `overall_score` from `reports/<TICKER>.json` (if exists).
- Optionally check Google News for a meaningful catalyst in the last 7 days. If NO catalyst exists, that's a HIGH-QUALITY signal.
- If the ticker isn't in the screener at all, append it to `data/screening_queue.csv` so the screening routine picks it up.

### 3b. Congressional clusters (WEEKLY) — fallback chain

The free HSW/SSW S3 buckets are dead (403). Try each source in order; accept the first that works. Do NOT block the rest of the run on congressional data — if all fail, write a note in `signals.json` and continue.

**Primary (legacy — likely 403):**
- House: `https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json`
- Senate: `https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json`

**Fallback 1: Official House Clerk disclosures**
- URL: `https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{YEAR}FD.zip`
- Download the current year's ZIP, extract the XML index, parse for transactions in the last 14 days where direction = `P` (purchase) and amount range ≥ $15K.
- House only — Senate has no equivalent bulk download.

**Fallback 2: Senate efdsearch (hard)**
- URL: `https://efdsearch.senate.gov/search/`
- Requires session cookies + POST queries. Only implement if Fallback 1 is insufficient on its own.

**Fallback 3: Capitol Trades web scrape**
- URL: `https://www.capitoltrades.com/trades`
- HTML pagination; look for the data-react-props attribute in the page source. Their BFF API is locked down (503).

**Fallback 4: Skip and document**
- Write `{"note": "congressional sources unavailable on YYYY-MM-DD; retry next run"}` into the `congressional` field of `signals.json`.
- The dashboard will show empty state — that's acceptable.

For whichever source succeeds:
- Filter: `transaction_date` within last 14 days, direction = purchase, amount mid-point ≥ $15,000.
- Group by ticker; keep tickers with ≥2 members.
- Annotate with committee assignments using `opportunities/committee_lookup.json` (refresh quarterly).
- Flag committee-relevant buys (Defense → defense names, Energy → energy, etc.) as higher-signal.

### 3c. Institutional 13F (QUARTERLY, ~45 days after each quarter end)

Watched fund list:
- Berkshire Hathaway, Bridgewater Associates, Pershing Square, Greenlight Capital, Third Point, Renaissance Technologies, Tiger Global, Coatue Management, Lone Pine Capital, Viking Global, Baupost Group, Appaloosa Management, Soros Fund Management, Icahn Enterprises, Pabrai Investment Funds, Akre Capital, Polen Capital, Wedgewood Partners, Sequoia Fund, Greenhaven Associates

On first quarterly run, look up each fund's CIK via SEC EDGAR search and cache as `opportunities/fund_cik_lookup.json`.

For each fund, pull the latest 13F-HR filing and compare to prior quarter:
- NEW position with market value ≥ $50M
- ADD ≥ 25% to existing position
- SELL ≥ 50% of existing position

Identify any ticker appearing in NEW or ADD across ≥2 funds.

On non-quarterly days, copy the prior quarter's institutional values forward.

### 3d. Cross-signal multiplier

If a ticker appears on ALL THREE signal types (insider + congressional + institutional) within a 90-day window, file as `"High Conviction"` regardless of pattern category — the alignment itself is the thesis.

### 3e. Write signals.json

Always write a fresh `opportunities/signals.json` even if some categories are empty (use `[]`):

```json
{
  "generated_at": "YYYY-MM-DD",
  "insider_clusters": [
    {"ticker": "ABCD", "name": "ABCD Corp", "buyers": 3, "total_value": 850000, "span_days": 12, "note": "CEO + CFO + Director; no news catalyst in 14 days"}
  ],
  "congressional": [
    {"ticker": "EFGH", "name": "EFGH Inc", "buyers": 2, "note": "Both members on House Energy & Commerce Committee"}
  ],
  "institutional": [
    {"ticker": "IJKL", "name": "IJKL Holdings", "buyers": 3, "note": "Pershing Square (NEW), Greenlight (+45%), Third Point (NEW)"}
  ]
}
```

---

## Step 4: Scan for Catalysts (ONLY after housekeeping is done)

### 4.0 Cadence check — are we going silent?

Before scanning for new catalysts, check when the last new opportunity was filed:

```python
import os, json
from datetime import date, datetime
OPP_DIR = 'opportunities'
SUPPORT = {'manifest.json', 'ledger.json', 'signals.json',
           'committee_lookup.json', 'fund_cik_lookup.json',
           'team_feedback.json', 'stalking.json'}
opps = [f for f in os.listdir(OPP_DIR)
        if f.endswith('.json') and f not in SUPPORT]
latest_date = None
for f in opps:
    with open(f'{OPP_DIR}/{f}') as fh:
        d = json.load(fh)
    di = d.get('date_identified')
    if di and (latest_date is None or di > latest_date):
        latest_date = di
days_silent = ((date.today() -
                datetime.strptime(latest_date, '%Y-%m-%d').date()).days
               if latest_date else 999)
print(f'Days since last new opp: {days_silent}')
```

**If `days_silent >= 14`**, you MUST surface at least 2 Stalking candidates this run, even if they only barely clear the Stalking bar (Step 5). The team needs visibility into what you're considering, not silence.

**If `days_silent >= 30`**, additionally lower the On Our Radar bar for THIS RUN ONLY: trade construction can be entirely qualitative ("rough entry zone is current price -10%, target +25%, stop -15%" is acceptable), and 1 secondary source is sufficient. Flag the opp with `"filed_under_cadence_relaxation": true` so the team knows the bar was lowered.

### 4.1 Catalyst scan

Do 3-5 web searches for current macro events:

1. `major geopolitical events supply chain disruption 2026`
2. `AI infrastructure spending earnings surprises 2026`
3. `commodity supply shock shortage 2026`
4. `technology sector rotation institutional money flow 2026`
5. `federal reserve policy impact sectors 2026`

Look for **asymmetric** setups — second/third-order effects the market hasn't fully priced. Match catalysts ONLY to stocks that already have screener reports in `reports/`.

---

## Step 5: Selection Criteria by Tier

### High Conviction — file ONLY if ALL hold

1. **Falsifiable catalyst within 18 months.** Specific date or event. "Secular trend" alone is insufficient.
2. **At least 2 primary sources.** Acceptable: SEC EDGAR filings, company IR / earnings transcripts, government data (EIA, BLS, BEA, Fed, USDA), peer-reviewed academic, named industry trade body. CNBC / Tech Insider / Motley Fool / Yahoo summaries count as "context" but NOT toward the 2-source minimum.
3. **All schema fields populated** (see Step 6).
4. **Concrete trade construction** — entry, target, stop, sizing all filled with current-market-grounded numbers.
5. **Ledger awareness** — if the proposed pattern has hit rate <40% over the last 10 closed opps with that pattern (computed in Step 1), require 3 primary sources AND a paragraph explaining why this case differs from the losing precedents.

### On Our Radar — file if MOST hold (relaxed bars marked ★)

1. Falsifiable catalyst within 18 months.
2. **★ At least 1 primary source** (was 2 for High Conviction). The second source can be a credible secondary (analyst report, industry publication, etc.).
3. All schema fields populated, BUT:
4. **★ Trade construction may be "best-available estimate"** with an explicit `confidence_note` field explaining what would need to firm up before promoting to High Conviction (e.g., "Entry zone assumes Q3 earnings doesn't surprise to the upside; stop level is approximate at -15% pending Aug 12 catalyst").
5. Ledger awareness applies as above.

### Stalking — file if ALL of these hold

1. Catalyst exists and is articulable (doesn't have to be dated yet).
2. Thesis paragraph (2-3 sentences) is specific — not "AI is growing."
3. At least 1 credible source of any type.
4. Ticker is in the screener OR added to the screening queue this run.
5. Doesn't duplicate an active opp's primary ticker AND theme.

Stalking entries go into `opportunities/stalking.json` (an array, NOT into the main manifest). Each entry:

```json
{
  "id": "kebab-slug",
  "title": "Short title",
  "added": "YYYY-MM-DD",
  "catalyst": "1-2 sentences",
  "thesis": "2-3 sentences explaining the angle",
  "tickers": ["TICK"],
  "source": {"title": "...", "url": "...", "date": "..."},
  "what_would_promote": "What additional evidence would move this to On Our Radar",
  "checks_remaining": "Which Step 5 criteria are not yet met"
}
```

If `stalking.json` does not exist yet, create it as `[]` on the first run that needs it.

### De-duplication — apply to all tiers

- An active opp already covers the same theme. **Amend the existing one** instead.
- **★ Updated concentration limit: 3 active opps per theme/sector** (was 2). Stalking entries don't count toward this.
- The primary ticker is already the lead in another active opp, unless the new angle is genuinely different on BOTH time horizon AND mechanism. (Does not apply to Stalking.)

### Source quality discipline

- ≤2 sources from any single publisher per opportunity (High Conviction and On Our Radar only).
- Heavy CNBC / Motley Fool reliance is a yellow flag for High Conviction; acceptable for On Our Radar with a `confidence_note`; fine for Stalking.
- Every source needs `title`, `publisher`, `date`, `url` for High Conviction and On Our Radar. Stalking can have just `title` and `url`.

---

## Step 6: Write the Opportunity JSON (schema)

```json
{
  "id": "descriptive-kebab-slug",
  "title": "Short Descriptive Title",
  "pattern": "Supply Chain|Supply Shock|Secular Trend|Regulatory|Cyclical",
  "conviction": "High Conviction|On Our Radar",
  "status": "active",
  "date_identified": "YYYY-MM-DD",
  "review_due": "YYYY-MM-DD (30-90 days out)",
  "summary": "1-2 sentence pitch.",
  "catalyst": "2-3 sentences describing the specific event or trend.",
  "thesis": "2-3 sentences explaining WHY this catalyst benefits specific stocks. Connect the dots; explain the second-order effect.",
  "counter_thesis": "Write the skeptic's argument in 3-5 sentences. The bear case. If you can't construct a credible one, the thesis isn't ready.",
  "tickers": ["TICK1", "TICK2"],
  "ticker_rationale": {
    "TICK1": "1-2 sentences. Cite specific data — market share, revenue exposure, competitive position.",
    "TICK2": "Same."
  },
  "trade_construction": {
    "entry_zone": "TICK1 $X-$Y, TICK2 $A-$B",
    "target_12mo": "TICK1 $Z (+W%), TICK2 $C (+D%)",
    "stop_loss": "TICK1 $Q (-R%), TICK2 $S (-T%)",
    "position_size_pct": "1.0-2.0% per name (High Conviction); 0.5-1.0% (On Our Radar)"
  },
  "confidence_note": "(On Our Radar only) What would need to firm up to promote this to High Conviction.",
  "filed_under_cadence_relaxation": false,
  "catalyst_calendar": [
    {"date": "YYYY-MM-DD", "ticker": "TICK1", "event": "Q2 earnings — guidance update"},
    {"date": "YYYY-MM-DD", "ticker": null, "event": "EU tariff vote"}
  ],
  "in_portfolio_status": {
    "TICK1": {"current_weight": 0.0, "target_weight": 1.5, "action": "Initiate"},
    "TICK2": {"current_weight": 1.2, "target_weight": 2.0, "action": "Add"}
  },
  "key_metrics": {
    "TICK1": {"stock_price": 0, "forward_pe": 0, "overall_score": 0, "recommendation": "BUY", "sleeve": "Growth"}
  },
  "risks": [
    "Specific risk that could invalidate the thesis",
    "Another specific risk"
  ],
  "invalidation": [
    {"trigger": "TICK1 backlog falls below 90 GW for 2 consecutive quarters"},
    {"trigger": "Hyperscaler aggregate capex cut by 20%+"}
  ],
  "timeframe": "3-6 months|6-12 months|12-24 months|12-36 months",
  "sources": [
    {"title": "...", "publisher": "...", "date": "YYYY-MM-DD", "url": "https://..."},
    {"title": "...", "publisher": "...", "date": "YYYY-MM-DD", "url": "https://..."}
  ]
}
```

**Rules:**
- IDs are lowercase kebab-case slugs.
- Tickers MUST have existing reports in `reports/`. Verify before including.
- `confidence_note` is REQUIRED on On Our Radar entries, omitted on High Conviction.
- `filed_under_cadence_relaxation` defaults to `false`; only set `true` when filed under the 30-day relaxation rule.
- Max 1-2 new High Conviction / On Our Radar opportunities per run. Stalking entries can be 2-5 per run as needed by the cadence rule.

---

## Step 7: Commit, Build, Deploy to Stock-Screener gh-pages

```bash
git add opportunities/*.json
git diff --cached --quiet || git commit -m "Opportunity finder: [brief description]"
git push -u origin HEAD

# Rebuild the static site
python3 main.py

# Deploy the changed files to Stock-Screener gh-pages via Git Data API
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

tree_items = []
# Deploy ONLY index.html (the opportunities tab renders here). Do NOT push
# output/manifest.json: that is the stock-screener manifest, owned by the daily
# screening pipeline. This task runs on a branch with stale stock reports, so
# rebuilding and pushing manifest.json here would overwrite the fresh manifest
# on gh-pages with stale screen_dates — the Dashboard staleness bug. The
# authoritative manifest is published by the screening deploy and the scheduled
# 'Run Stock Screener' workflow, both of which build from current reports.
for fpath in ['output/index.html']:
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
print('Deployed opportunities to Stock-Screener gh-pages.')
"
```

---

## Step 7.5: Merge claude/ branch back to main (prevents orphaned work)

Scheduled tasks run on `claude/...` work branches. Without merging back, opportunity files (and the ledger, signals, and stalking files) created today exist ONLY on the work branch — never reaching main. The next run starts from a stale main and has to recover missing files from the Dashboard.

```bash
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
  git push -u origin "$CURRENT_BRANCH"

  git checkout main
  git pull origin main --ff-only

  if git merge "$CURRENT_BRANCH" --no-ff -m "Merge $CURRENT_BRANCH: opportunity finder run $(date +%Y-%m-%d)"; then
    git push origin main
    echo "Merged $CURRENT_BRANCH → main"
  else
    echo "WARN: merge to main had conflicts. Aborting merge; work is safe on $CURRENT_BRANCH."
    git merge --abort
  fi

  git checkout "$CURRENT_BRANCH"
fi
```

Never use `--force` here — that can destroy other branches' work. If conflicts ever arise, resolve manually and re-run.

---

## Step 8: Sync All Opportunity Files to Dashboard

The Dashboard reads from its own `public/opportunities/` folder. Sync the entire opportunities directory AND **always regenerate `manifest.json`** — without it the dashboard has no list of opportunity IDs to fetch.

```bash
if [ -z "${GITHUB_PUSH_TOKEN:-}" ] && [ -f .env ]; then source .env && export GITHUB_PUSH_TOKEN; fi

DASH_DIR=$(mktemp -d)
git clone --depth=1 "https://${GITHUB_PUSH_TOKEN}@github.com/richacarson/Dashboard.git" "$DASH_DIR"

SUPPORT_FILES="manifest.json ledger.json signals.json stalking.json committee_lookup.json fund_cik_lookup.json team_feedback.json"

# Defensive recovery: pull back any opp files the Dashboard has that
# we don't have locally (parallel routines, etc.) BEFORE wiping
for f in "$DASH_DIR/public/opportunities/"*.json; do
  fname=$(basename "$f")
  if echo "$SUPPORT_FILES" | grep -qw "$fname"; then continue; fi
  if [[ ! -f "opportunities/$fname" ]]; then
    cp "$f" "opportunities/$fname"
    echo "Recovered $fname from Dashboard (missing locally)"
  fi
done
git add opportunities/*.json
git diff --cached --quiet || git commit -m "Recover opportunity files from Dashboard"

# Wipe and re-copy
rm -f "$DASH_DIR/public/opportunities/"*.json
cp opportunities/*.json "$DASH_DIR/public/opportunities/"

# CRITICAL: regenerate manifest.json from the opp files actually present
# in the Dashboard folder. The opp files are the source of truth — the
# manifest is just an index. Without this step the dashboard cannot
# list opportunities.
python3 -c "
import json, os
SUPPORT = {'manifest.json', 'ledger.json', 'signals.json', 'stalking.json',
           'committee_lookup.json', 'fund_cik_lookup.json',
           'team_feedback.json'}
opp_dir = '$DASH_DIR/public/opportunities'
ids = sorted([
    os.path.splitext(f)[0]
    for f in os.listdir(opp_dir)
    if f.endswith('.json') and f not in SUPPORT
])
with open(os.path.join(opp_dir, 'manifest.json'), 'w') as out:
    json.dump(ids, out, indent=2)
print(f'Generated manifest.json with {len(ids)} opportunity IDs')
"

cd "$DASH_DIR"
git add public/opportunities/
if ! git diff --cached --quiet; then
  git config user.name "claude-task[bot]"
  git config user.email "claude-task[bot]@users.noreply.github.com"
  git commit -m "Sync opportunities from Stock-Screener"
  git push
  echo "Synced opportunities to Dashboard."
else
  echo "No opportunity changes to sync."
fi
cd -
rm -rf "$DASH_DIR"
```

---

## Step 9: Report Results

```bash
python3 -c "
import json, os
from pathlib import Path

OPP_DIR = Path('opportunities')
SUPPORT = {'manifest.json', 'ledger.json', 'signals.json', 'stalking.json',
           'committee_lookup.json', 'fund_cik_lookup.json',
           'team_feedback.json'}

active = sorted([f for f in os.listdir(OPP_DIR)
                 if f.endswith('.json') and f not in SUPPORT])
ledger = json.load(open(OPP_DIR / 'ledger.json')) if (OPP_DIR / 'ledger.json').exists() else []
stalking = json.load(open(OPP_DIR / 'stalking.json')) if (OPP_DIR / 'stalking.json').exists() else []
signals = json.load(open(OPP_DIR / 'signals.json')) if (OPP_DIR / 'signals.json').exists() else None

# Count active opps by conviction
hc = ar = 0
for f in active:
    with open(OPP_DIR / f) as fh:
        d = json.load(fh)
    c = d.get('conviction', '')
    if c == 'High Conviction': hc += 1
    elif c == 'On Our Radar': ar += 1

print(f'Active opportunities: {len(active)} (High Conviction: {hc}, On Our Radar: {ar})')
print(f'Stalking candidates: {len(stalking)}')
print(f'Closed (ledger): {len(ledger)}')
if signals:
    print(f'Signals refreshed: insider={len(signals.get(\"insider_clusters\",[]))}, congressional={len(signals.get(\"congressional\",[]))}, institutional={len(signals.get(\"institutional\",[]))}')
"
```

---

## Important Notes

- **Quality over quantity, but visibility over silence.** One great High Conviction opp per week beats five mediocre ones — but if the routine has been silent for two weeks, surface what you're stalking.
- **Housekeeping before new ideas.** Most days, the highest-value action is updating an existing opp, not adding a new one.
- **Be specific.** "AI is growing" is not a thesis. "NVIDIA's Rubin platform requires 3.2T optical links, creating $5B TAM for AEC suppliers" is a thesis.
- **Check your work.** Verify tickers have reports in `reports/`. Verify primary sources actually exist and aren't broken links.
- **Don't duplicate.** Run the de-dup check before opening anything new. Concentration limit is 3-per-theme on active opps (Stalking doesn't count).
- **Honor the ledger.** If a pattern is failing, raise the bar — don't pretend the precedents don't exist.
- **Read team feedback.** If `team_feedback.json` exists, recent entries should influence what you file today.
- **Respect the cadence rule.** 14 days silent → must surface ≥2 Stalking candidates. 30 days silent → On Our Radar bar drops; flag any opp filed under that relaxation.
- **Always merge to main (Step 7.5).** Non-optional. Skipping it causes the orphaned-branches problem.
- **Always regenerate manifest.json (Step 8).** Non-optional. Skipping it makes the dashboard unable to list opportunities.
