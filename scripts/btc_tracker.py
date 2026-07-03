#!/usr/bin/env python3
"""BTC tracker CLI.

Usage:
    python3 scripts/btc_tracker.py fetch                 # pull from APIs + build
    python3 scripts/btc_tracker.py import-csv FILE...    # import exchange CSVs + build
    python3 scripts/btc_tracker.py add --date 2024-01-15 --btc 0.5 \
        --usd 21500 [--source manual] [--type buy]       # manual lump-sum entry
    python3 scripts/btc_tracker.py build                 # rebuild dashboard only

See BTC_TRACKER.md for API key setup.
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from btc_tracker import build, config, coinbase, csv_import, kraken, store


def cmd_fetch(_: argparse.Namespace) -> None:
    fetched = 0
    kraken_creds = config.kraken_credentials()
    if kraken_creds:
        print("Fetching Kraken trades + transfers...")
        txs = kraken.fetch_all(*kraken_creds)
        added, total = store.merge(txs)
        print(f"  Kraken: {len(txs)} transactions ({added} new)")
        fetched += len(txs)
    else:
        print("  Kraken: no credentials (set KRAKEN_API_KEY / KRAKEN_API_SECRET)")

    coinbase_creds = config.coinbase_credentials()
    if coinbase_creds:
        print("Fetching Coinbase transactions...")
        txs = coinbase.fetch_all(*coinbase_creds)
        added, total = store.merge(txs)
        print(f"  Coinbase: {len(txs)} transactions ({added} new)")
        fetched += len(txs)
    else:
        print("  Coinbase: no credentials (set COINBASE_KEY_FILE)")

    if not fetched and not store.load():
        print("\nNo data. Add API keys to .env or use import-csv. See BTC_TRACKER.md")
        return
    cmd_build(_)


def cmd_import_csv(args: argparse.Namespace) -> None:
    for file in args.files:
        txs = csv_import.import_file(file)
        added, total = store.merge(txs)
        print(f"  {Path(file).name}: {len(txs)} transactions ({added} new)")
    cmd_build(args)


def cmd_add(args: argparse.Namespace) -> None:
    ts = (
        datetime.strptime(args.date, "%Y-%m-%d")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )
    tx = {
        "id": f"manual:{args.date}-{args.type}-{args.btc}",
        "source": args.source,
        "type": args.type,
        "timestamp": ts,
        "btc_amount": args.btc,
        "usd_amount": args.usd,
        "fee_usd": 0.0,
        "fee_btc": 0.0,
        "note": args.note or "manual entry",
    }
    store.add_manual(tx)
    print(f"Added {args.type}: {args.btc} BTC for ${args.usd:,.2f} on {args.date}")
    cmd_build(args)


def cmd_publish(args: argparse.Namespace) -> None:
    """Build, then push the dashboard HTML to the password-gated live URL."""
    import requests

    url = config.get_env("BTC_DASHBOARD_URL").rstrip("/")
    token = config.get_env("BTC_PUBLISH_TOKEN")
    if not url or not token:
        sys.exit("Set BTC_DASHBOARD_URL and BTC_PUBLISH_TOKEN in .env")
    path = build.build()
    html = Path(path).read_text()
    resp = requests.post(
        f"{url}/publish",
        headers={"x-publish-token": token},
        data=html.encode(),
        timeout=60,
    )
    resp.raise_for_status()
    if resp.text != "ok":
        sys.exit(f"Publish failed: {resp.text}")
    print(f"Published {len(html):,} bytes to {url}")


def cmd_build(_: argparse.Namespace) -> None:
    txs = store.load()
    if not txs:
        print("No transactions stored yet.")
    path = build.build()
    print(f"\nDashboard: {path}")
    print(f"  ({len(txs)} transactions; open in a browser)")


def main() -> None:
    parser = argparse.ArgumentParser(description="BTC cost-basis tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("fetch", help="pull from exchange APIs, then build")

    p_csv = sub.add_parser("import-csv", help="import exchange CSV exports")
    p_csv.add_argument("files", nargs="+")

    p_add = sub.add_parser("add", help="add a manual transaction")
    p_add.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_add.add_argument("--btc", type=float, required=True)
    p_add.add_argument("--usd", type=float, required=True)
    p_add.add_argument(
        "--type", default="buy", choices=["buy", "sell", "withdrawal", "deposit"]
    )
    p_add.add_argument("--source", default="manual")
    p_add.add_argument("--note", default="")

    sub.add_parser("build", help="rebuild the dashboard from stored data")
    sub.add_parser("publish", help="build and push to the live dashboard URL")

    args = parser.parse_args()
    {
        "fetch": cmd_fetch,
        "import-csv": cmd_import_csv,
        "add": cmd_add,
        "build": cmd_build,
        "publish": cmd_publish,
    }[args.command](args)


if __name__ == "__main__":
    main()
