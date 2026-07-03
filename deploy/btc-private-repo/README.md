# BTC Tracker

Private Bitcoin cost-basis tracker. Pulls full trade history from Kraken and
Coinbase with **read-only** API keys, treats sends to Phantom as transfers
(not sales — cost basis carries over), and publishes a password-gated
dashboard, refreshed automatically every day by GitHub Actions.

**Live dashboard:** https://ocovjbvrtbxptqtucyqw.supabase.co/functions/v1/btc-dashboard

## How it works

```
GitHub Actions (daily 13:23 UTC)
  └─ scripts/btc_tracker.py fetch     ← Kraken + Coinbase APIs (read-only)
  └─ scripts/btc_tracker.py publish   ← POSTs built HTML to the Supabase
                                        edge function (publish token)
Supabase edge function "btc-dashboard" (project: Trade Instructions)
  └─ serves a login page; password → SHA-256 checked against btc_config
  └─ valid session cookie (30 days) → serves HTML from btc_dashboard table
```

The dashboard HTML lives in a Supabase table with row-level security enabled
and no policies — nothing is publicly readable; only the edge function
(service role) touches it. The login password is stored only as a SHA-256
hash. Wrong-password attempts are delayed 600ms.

## Required GitHub secrets (Settings → Secrets and variables → Actions)

| Secret | Value |
|--------|-------|
| `KRAKEN_API_KEY` | Kraken API key (Query Funds / Query closed orders & trades / Query ledger entries ONLY) |
| `KRAKEN_API_SECRET` | Kraken private key |
| `COINBASE_API_KEY_NAME` | `name` field from the downloaded `cdp_api_key.json` (looks like `organizations/…/apiKeys/…`) |
| `COINBASE_API_PRIVATE_KEY` | `privateKey` field from `cdp_api_key.json` (the whole PEM, newlines fine) |
| `BTC_PUBLISH_TOKEN` | Publish token for the edge function |

Optional **variable** (not secret): `PHANTOM_BTC_ADDRESSES` — comma-separated
BTC addresses from Phantom (both the `bc1q…` and `bc1p…` ones) for the
on-chain balance cross-check.

## Local usage

```bash
pip install -r requirements.txt
cp .env.example .env        # fill in keys

python3 scripts/btc_tracker.py fetch        # pull APIs + build private/btc_dashboard.html
python3 scripts/btc_tracker.py publish      # build + push to the live URL
python3 scripts/btc_tracker.py import-csv trades.csv ledgers.csv coinbase.csv
python3 scripts/btc_tracker.py add --date 2021-04-15 --btc 0.25 --usd 15000
```

Everything is deduped by transaction ID — re-running fetch/import is always safe.

Manual entries land in `data/btc_manual.json`, which IS committed in this
private repo so the daily Actions run includes them. The API cache
(`data/btc_transactions.json`) is not committed; Actions re-fetches the full
history each run.

## Changing the dashboard password

In the Supabase SQL editor (project `ocovjbvrtbxptqtucyqw`):

```sql
update btc_config
set password_hash = encode(sha256('YOUR-NEW-PASSWORD'::bytea), 'hex'),
    -- rotating the session secret logs out all existing sessions:
    session_secret = encode(gen_random_bytes(32), 'hex'),
    updated_at = now()
where id = 1;
```

## Cost basis method

Average cost, fees included in basis. Sells realize P&L at the running
average. Withdrawals to Phantom are location moves, not disposals; only the
BTC network fee reduces holdings. Not tax advice — for US tax lots you'd
want FIFO/spec-ID, and `data/btc_transactions.json` has everything needed.
