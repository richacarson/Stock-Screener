# IOWN Stock Screener — Daily Screening Task

You are running a scheduled daily task for the IOWN Stock Screener project at `/home/user/Stock-Screener`. Your job is to generate IOWN Return on Intention stock analysis reports for the next batch of stocks.

**Two modes:** If unscreened stocks remain in the queue, screen those first. Once the entire queue is screened, cycle back and **re-screen the oldest reports** (by `screen_date`) to keep data fresh.

## Step 0: Sync Reports from Prior Scheduled Runs

**CRITICAL:** Each scheduled task runs on its own `claude/` branch. If prior runs generated reports but those weren't merged back to the default branch, you'll re-screen the same stocks. Before determining what to screen, pull any reports from recent screening branches:

```bash
# Fetch all remote branches first — without this, we won't see branches from prior scheduled runs
git fetch origin

# List recent daily-screening branches and merge their reports
python3 -c "
import subprocess, json

# Get remote branches matching daily-screening pattern
result = subprocess.run(['git', 'branch', '-r'], capture_output=True, text=True)
screening_branches = [b.strip() for b in result.stdout.splitlines()
                      if 'daily-screening' in b and b.strip().startswith('origin/')]

if not screening_branches:
    print('No prior screening branches found.')
else:
    print(f'Found {len(screening_branches)} screening branches, checking for new reports...')
    for branch in sorted(screening_branches):
        # Check what reports this branch has that we don't
        diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD', branch, '--', 'reports/'],
                              capture_output=True, text=True)
        new_files = [f for f in diff.stdout.splitlines() if f.startswith('reports/') and f.endswith('.json')]
        if new_files:
            # Only pull reports that don't exist locally
            import os
            truly_new = [f for f in new_files if not os.path.exists(f)]
            if truly_new:
                print(f'  {branch}: {len(truly_new)} new reports — pulling...')
                subprocess.run(['git', 'checkout', branch, '--'] + truly_new)
            else:
                print(f'  {branch}: reports already present locally')
        else:
            print(f'  {branch}: no new reports')
"

# If new reports were pulled, commit them
git add reports/*.json 2>/dev/null
git diff --cached --quiet || git commit -m "Sync reports from prior scheduled screening runs"
```

## Step 1: Determine What to Screen

Batch selection lives in `scripts/select_batch.py` (tested + version-controlled)
so the rotation logic stays correct. It returns one of two modes:

- **NEW** — next unscreened stocks from `data/screening_queue.csv`, in volume order.
- **REFRESH** — once the queue is exhausted, the **full report set** ranked by
  oldest `screen_date` first. This includes seed/portfolio tickers that were
  never in the queue (NVDA, TSM, AMD, QCOM, …), so the *entire* universe keeps
  cycling instead of those names getting stuck.

Run this to print the next 50 stocks (with inspire data) to screen:

```bash
python3 -c "
import csv
from scripts.select_batch import select_batch

mode, batch_tickers = select_batch(count=50)
print(f'MODE: {mode}')
print(f'This batch: {len(batch_tickers)} stocks')
print()

# Queue lookup for volume context (best-effort)
queue_lookup = {}
try:
    with open('data/screening_queue.csv', newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            queue_lookup[r['symbol']] = r
except FileNotFoundError:
    pass

# Load inspire data
with open('data/inspire_insight_scores.csv', encoding='utf-8-sig') as f:
    inspire = {r['ticker']: r for r in csv.DictReader(f)}

# Print batches of 5 with inspire data
for i in range(0, len(batch_tickers), 5):
    chunk = batch_tickers[i:i+5]
    print(f'=== BATCH {i//5 + 1} ({len(chunk)} stocks) ===')
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

Process **10 batches of 5 stocks each**, launching agents **ONE AT A TIME** (never parallel). Wait for each agent to complete before starting the next.

Batches of 5 are critical — larger batches (10-20 stocks) cause agents to hit context limits from web search results and fail mid-batch. 5 stocks × 3 web searches = 15 searches per agent, which fits comfortably.

For each batch, launch an agent with the prompt below, filling in the stock list and inspire data from Step 1's output:

---

### Agent Prompt Template

You are generating IOWN Return on Intention stock analysis reports. Generate a `reports/{TICKER}.json` file for each of the following stocks. Work through them one at a time.

#### YOUR STOCKS (Batch N)
{List each ticker, e.g.: BAC, BBD, AMD, CSCO, PFE}

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
5. Write `reports/{TICKER}.json` — match the exact JSON structure of existing reports in `reports/`. Read any existing report (e.g., `reports/AAPL.json`) for the schema.

#### SCORING RULES

**Sub-score labels (/10):** STRONG/SAFE/LOW RISK = 7+, DEVELOPING/MODERATE/NEUTRAL = 4-6, WEAK/AT RISK/HIGH RISK = 1-3

**Overall score (0-100) — 3 dimensions, weighted:**
```
overall = avg(innovation, inspiration, infrastructure) / 10 * 50 + ai_resilience / 10 * 25 + infinite_game_overall / 10 * 25
```
Faith Alignment: 0% weight (display only). Recommendation: BUY 80+, HOLD 60-79, WATCH 40-59, SELL <40.

**Sleeve:** Current IOWN holdings forced from `data/portfolios.json`. Others: Dividend (5+ yr history AND yield > 2%), Growth (everything else including revenue growth > 15% YoY).

**HARD RULES:**
- **LIQUIDITY FLOOR**: If `avg_daily_volume × stock_price < $1,000,000` → Infrastructure score = **0**
- **Infrastructure is calculated mechanically** from financial metrics — see SCREENING.md for the full algorithm
- **Faith alignment labels**: ALIGNED (>25), MIXED (-25 to 25), MISALIGNED (<-25)
- **Inspire data**: MUST come from the CSV data provided above. Do NOT web search for inspire scores.
- **screen_date**: Use today's date in YYYY-MM-DD format.
- **Source references**: Include `[1]`, `[2]`, etc. in analysis text to cite sources. `sources` array is 1-indexed.

#### QUALITY STANDARDS
- Every score MUST cite specific evidence from research. No generic statements.
- Analysis: 2-3 dense sentences per field, no filler words.
- Use the FULL scoring range honestly — a score of 3-4 is appropriate for struggling companies.
- If yfinance fails for a ticker, proceed with web research only. Use `null` for unavailable metrics.
- Write each report to `/home/user/Stock-Screener/reports/{TICKER}.json`
- Process ALL 5 stocks in your batch — do not skip any.

---

## Step 3: After All Batches Complete

Once all 10 agents have finished (or however many batches were needed for this run):

```bash
# Rebuild the static site from all reports
# CRITICAL: This regenerates manifest.json with updated screen_date values.
# The Dashboard uses manifest.json for the stock list — if you skip this,
# the Dashboard will show stale dates even though report JSONs are updated.
python3 main.py

# Gate the deploy on a consistent manifest. Fails if any manifest screen_date
# lags its report file, so a drifted manifest is never published.
python3 scripts/verify_manifest.py

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

# Push to the current branch
git push -u origin HEAD
```

## Step 4: Deploy to GitHub Pages

**IMPORTANT:** Use the GitHub Git Data API to deploy the `output/` directory to `gh-pages`. Do NOT commit report JSON files directly to `gh-pages` — that branch should only contain built output (HTML, manifest.json, and the `output/reports/` copies). Source reports belong in `reports/` on the working branch.

```bash
# Load token from environment or .env file
if [ -z "${GITHUB_PUSH_TOKEN:-}" ] && [ -f .env ]; then source .env && export GITHUB_PUSH_TOKEN; fi

# Deploy using the Git Data API — only deploy new/changed report HTML files and index.html
# Do NOT redeploy all files every time. Use base_tree to add to existing gh-pages content.
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

# Collect only HTML, JSON manifest, and report JSONs (skip docx for speed)
output_dir = Path('output')
files = []
for root, dirs, filenames in os.walk(output_dir):
    for fname in filenames:
        fpath = Path(root) / fname
        rel = str(fpath.relative_to(output_dir))
        if rel.startswith('docx/'): continue
        files.append((rel, fpath))

print(f'Deploying {len(files)} files...')
tree_items = []
for i, (rel, fpath) in enumerate(files):
    content = base64.b64encode(fpath.read_bytes()).decode()
    blob = api('POST', '/git/blobs', {'content': content, 'encoding': 'base64'})
    tree_items.append({'path': rel, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
    if (i + 1) % 500 == 0 or i == len(files) - 1:
        print(f'  Blobs: {i+1}/{len(files)}')

base_sha = None
for start in range(0, len(tree_items), 200):
    chunk = tree_items[start:start+200]
    payload = {'tree': chunk}
    if base_sha: payload['base_tree'] = base_sha
    result = api('POST', '/git/trees', payload)
    base_sha = result['sha']

parent_sha = api('GET', '/git/ref/heads/gh-pages')['object']['sha']
commit = api('POST', '/git/commits', {'message': 'Deploy: daily screening update', 'tree': base_sha, 'parents': [parent_sha]})
api('PATCH', '/git/refs/heads/gh-pages', {'sha': commit['sha'], 'force': True})
print('Deployed to gh-pages!')
"
```

## Step 4.5: Merge Screening Reports Back to main

**CRITICAL — prevents orphaned work and a stuck rotation.** Scheduled runs work
on `claude/...` branches. If today's reports are never merged back to `main`,
the next run starts from a stale `main`, re-screens the same oldest stocks, and
the rotation never advances — exactly the "screener isn't progressing / has
gaps" failure. Merge today's reports back (same safe pattern as the opportunity
finder: `--no-ff`, abort on conflict, never `--force`).

```bash
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
  git push -u origin "$CURRENT_BRANCH"

  git checkout main
  git pull origin main --ff-only

  if git merge "$CURRENT_BRANCH" --no-ff -m "Merge $CURRENT_BRANCH: daily screening $(date +%Y-%m-%d)"; then
    git push origin main
    echo "Merged $CURRENT_BRANCH → main"
  else
    echo "WARN: merge to main had conflicts. Aborting merge; work is safe on $CURRENT_BRANCH."
    git merge --abort
  fi

  git checkout "$CURRENT_BRANCH"
fi
```

This makes Step 0's cross-branch report sync a safety net rather than the only
way prior runs' reports reach the next run.

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

# Find oldest report date across the FULL report set (not just queue members)
# so the rotation's true oldest is reported, including seed/portfolio tickers.
oldest_date = None
for rf in os.listdir('reports'):
    if not rf.endswith('.json'): continue
    try:
        with open(f'reports/{rf}') as fh:
            sd = json.load(fh).get('screen_date','')
            if oldest_date is None or sd < oldest_date:
                oldest_date = sd
    except: pass

print(f'Reports total: {len(done)}')
print(f'Queue remaining (unscreened): {len(remaining)}')
if remaining:
    print(f'Estimated days to finish first pass: {len(remaining) // 50 + (1 if len(remaining) % 50 else 0)} (at 2 runs/day)')
else:
    print(f'All stocks screened! Now in REFRESH mode (re-screening oldest first)')
print(f'Oldest report date: {oldest_date or \"N/A\"}')
print(f'Full refresh cycle: ~{len(queue) // 100 + 1} days (2 runs/day x 50 each)')
"
```

## Important Notes

- **NEVER launch agents in parallel** — sequential only (one at a time) to avoid rate limits
- **Batch size MUST be 5** — larger batches (10-20) cause agents to hit context limits from web searches and fail
- **NEVER web search for Inspire scores** — always use the CSV data
- **Always use today's date** for `screen_date`
- If a batch agent fails or times out, note which stocks were missed and include them in the next batch
- The queue is sorted by avg daily volume descending — always process in queue order (most liquid first)
