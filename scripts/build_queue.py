"""Build the screening queue: fetch avg daily volume for all stocks,
filter to >= 950K volume, exclude already-screened, sort by volume desc.

Output: data/screening_queue.csv

This script takes ~30-60 min due to yfinance lookups. It only needs to
run once — the queue is then consumed by the daily screening task.
"""

import csv
import os
import sys
import time

import yfinance as yf

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
US_STOCKS_CSV = os.path.join(DATA_DIR, "us_stocks.csv")
QUEUE_CSV = os.path.join(DATA_DIR, "screening_queue.csv")

VOLUME_THRESHOLD = 950_000


def get_existing_tickers() -> set[str]:
    """Get tickers that already have reports."""
    return {
        f.replace(".json", "")
        for f in os.listdir(REPORTS_DIR)
        if f.endswith(".json")
    }


def load_universe() -> list[dict]:
    """Load all stocks from us_stocks.csv."""
    with open(US_STOCKS_CSV, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def fetch_volume_batch(tickers: list[str]) -> dict[str, int | None]:
    """Fetch avg daily volume for a batch of tickers."""
    results = {}
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            vol = info.get("averageVolume") or info.get("averageDailyVolume10Day")
            results[ticker] = int(vol) if vol else None
        except Exception:
            results[ticker] = None
    return results


def build_queue():
    """Build the screening queue."""
    existing = get_existing_tickers()
    universe = load_universe()

    # Get the ticker column name (may have BOM)
    ticker_key = list(universe[0].keys())[0]  # First column is ticker

    print(f"Universe: {len(universe)} stocks")
    print(f"Already screened: {len(existing)}")

    # Pre-filter: skip obvious non-equities
    candidates = []
    skipped_types = 0
    for row in universe:
        ticker = row[ticker_key].strip()
        name = row.get("name", "").lower()

        # Skip rights, warrants, units
        if any(
            name.endswith(suffix)
            for suffix in (" right", " rights", " warrant", " warrants", " unit", " units")
        ):
            skipped_types += 1
            continue

        # Skip if already screened
        if ticker in existing:
            continue

        candidates.append({
            "ticker": ticker,
            "name": row.get("name", ticker),
            "market_cap": row.get("market_cap", ""),
        })

    print(f"Candidates after pre-filter: {len(candidates)} (skipped {skipped_types} non-equities)")
    print(f"Fetching volume data from yfinance...")

    # Fetch volumes in batches
    batch_size = 20
    queue = []
    processed = 0

    for i in range(0, len(candidates), batch_size):
        batch = candidates[i : i + batch_size]
        batch_tickers = [c["ticker"] for c in batch]
        volumes = fetch_volume_batch(batch_tickers)

        for candidate in batch:
            ticker = candidate["ticker"]
            vol = volumes.get(ticker)
            if vol is not None and vol >= VOLUME_THRESHOLD:
                candidate["avg_daily_volume"] = vol
                queue.append(candidate)

        processed += len(batch)
        above = len(queue)
        if processed % 100 == 0 or processed == len(candidates):
            print(f"  Processed {processed}/{len(candidates)} — {above} pass volume filter")

        # Small delay to be nice to Yahoo Finance
        if i + batch_size < len(candidates):
            time.sleep(0.5)

    # Sort by volume descending
    queue.sort(key=lambda x: x["avg_daily_volume"], reverse=True)

    # Write queue CSV
    with open(QUEUE_CSV, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["ticker", "name", "avg_daily_volume", "market_cap"]
        )
        writer.writeheader()
        writer.writerows(queue)

    print(f"\nQueue written to {QUEUE_CSV}")
    print(f"Total stocks in queue: {len(queue)}")
    if queue:
        print(f"Top 10 by volume: {', '.join(q['ticker'] for q in queue[:10])}")
        print(f"At 100 stocks/day: ~{len(queue) // 100 + 1} days to complete")


if __name__ == "__main__":
    build_queue()
