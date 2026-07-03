# BTC Tracker — Setup & Usage

A private Bitcoin cost-basis dashboard. It pulls your full trade history from
Kraken and Coinbase with **read-only** API keys, treats sends to Phantom as
transfers (not sales — your cost basis carries over), and computes:

- Total BTC held (across Kraken, Coinbase, and Phantom)
- Average cost per BTC (**fees included**) and total invested
- Unrealized and realized P&L (average-cost method)
- Where your BTC lives, with an optional on-chain cross-check of your
  Phantom addresses via mempool.space

**Privacy:** the dashboard builds to `private/btc_dashboard.html`, and all
transaction data lives in `data/btc_transactions.json` / `data/btc_manual.json`.
All of these are **gitignored** and are never deployed to the public
GitHub Pages site. Keep it that way.

## Quick start

```bash
pip install -r requirements.txt

# after adding keys to .env (see below):
python3 scripts/btc_tracker.py fetch

# then open private/btc_dashboard.html in a browser
```

Re-running `fetch` any time is safe — transactions are deduped by exchange
transaction ID, so it just picks up your new daily buys.

## Getting the API keys

Both keys are **read-only**. Never create keys with trade or withdrawal
permissions for this — the tracker doesn't need them and you don't want a
key that can move funds sitting in a `.env` file.

### Kraken (read-only key)

1. Log in at kraken.com → click your name (top right) → **Settings** → **API**
   (or go directly to https://pro.kraken.com/app/settings/api).
2. **Create API key**.
3. Give it a name like `btc-tracker-readonly`.
4. Under permissions, enable ONLY:
   - **Funds → Query** (balances)
   - **Orders & Trades → Query closed orders & trades**
   - **Data → Query ledger entries** (needed to see your withdrawals to Phantom)
   - Leave everything else OFF — especially anything under Trade, Withdraw, or Transfer.
5. Generate the key and copy both values into `.env`:

```
KRAKEN_API_KEY=your-api-key
KRAKEN_API_SECRET=your-private-key
```

### Coinbase (read-only CDP key)

Coinbase now issues API keys through the Coinbase Developer Platform:

1. Go to https://portal.cdp.coinbase.com/access/api (sign in with your
   normal Coinbase account).
2. **Create API key**.
3. Name it `btc-tracker-readonly` and set the permission to **View** only.
4. Download the key file (`cdp_api_key.json`) when prompted — this is the
   only time you can. Store it somewhere private, e.g. `~/.keys/cdp_api_key.json`.
5. Point `.env` at it:

```
COINBASE_KEY_FILE=/Users/you/.keys/cdp_api_key.json
```

(Alternatively set `COINBASE_API_KEY_NAME` and `COINBASE_API_PRIVATE_KEY`
directly, with `\n` escapes in the PEM.)

### Phantom (no key needed — just addresses)

Phantom is self-custody, so there's no API key. The tracker already knows how
much BTC you sent there from the exchange withdrawal records. To also verify
against the chain:

1. Open Phantom → click your Bitcoin account → **Receive** → copy the BTC
   address. Note: Phantom shows both a **Native SegWit** (`bc1q…`) and a
   **Taproot** (`bc1p…`) address — grab both.
2. Add them to `.env` (comma-separated):

```
PHANTOM_BTC_ADDRESSES=bc1q...,bc1p...
```

Heads-up: mempool.space balance checks are per-address. If Phantom rotates
receive addresses on you, list every address you've received to. If the
on-chain total doesn't match the computed transfer total, the dashboard
flags it instead of guessing.

## No API keys? Use CSV exports

- **Kraken**: History → Export → export **Trades** and **Ledgers** as CSV.
- **Coinbase**: Profile → Statements → generate a **Transaction statement** (CSV, all time).

```bash
python3 scripts/btc_tracker.py import-csv trades.csv ledgers.csv coinbase.csv
```

This is also the accuracy backstop for old Coinbase buys: the statement CSV
has exact fee-inclusive totals, while the Coinbase API reports some legacy
buys at spot value (fees approximated).

## Manual entries

For anything not covered (a gift, an OTC buy, an exchange you closed):

```bash
python3 scripts/btc_tracker.py add --date 2021-04-15 --btc 0.25 --usd 15000
```

## Commands

| Command | What it does |
|---------|--------------|
| `fetch` | Pull from Kraken + Coinbase APIs, merge, rebuild dashboard |
| `import-csv FILE...` | Import exchange CSV exports, merge, rebuild |
| `add --date --btc --usd` | Add a manual transaction, rebuild |
| `build` | Rebuild the dashboard from stored data only |

## How cost basis is computed

**Average-cost method, fees included in basis:**

- **Buys** add `total paid (including fees)` to your cost basis.
- **Sells** remove BTC at the running average cost; the difference vs. net
  proceeds is realized P&L. The average cost of what remains is unchanged.
- **Withdrawals to Phantom are NOT sales.** The BTC just changes location;
  your basis carries over. Only the small BTC network fee reduces holdings.
- **Deposits** are assumed to be your own BTC coming back from self-custody.

This matches the "average cost" figure most portfolio apps show. It is not
tax advice — for US tax lots you'd want per-lot (FIFO/spec-ID) accounting;
the raw data in `data/btc_transactions.json` has everything needed if that's
ever wanted.
