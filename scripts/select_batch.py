#!/usr/bin/env python3
"""Select the next batch of tickers for the daily screening task.

Two modes:
  NEW     — stocks still in the screening queue that don't yet have a report.
            Returned in queue order (the queue is sorted by avg daily volume
            descending, so the most liquid names are screened first).
  REFRESH — once every queued stock has a report, cycle through *all* existing
            reports by oldest ``screen_date`` first so the whole universe stays
            fresh.

Bug fix (rotation got stuck): REFRESH mode used to restrict candidates to
tickers present in ``data/screening_queue.csv``. Seed and portfolio tickers
that were screened *before* the queue was built (e.g. NVDA, TSM, AMD, QCOM)
are never written to the queue, so they were skipped forever and their reports
went stale. REFRESH now ranks the full report set, so every ticker re-enters
the rotation regardless of queue membership.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

DEFAULT_QUEUE = Path("data/screening_queue.csv")
DEFAULT_REPORTS = Path("reports")
DEFAULT_COUNT = 50

# Used when a report has no (or an unreadable) screen_date so it sorts to the
# front of the REFRESH rotation and gets refreshed first.
_EPOCH = "0000-00-00"


def _load_queue(queue_csv: Path) -> list[str]:
    """Return queue symbols in file order (already sorted by volume desc)."""
    if not queue_csv.exists():
        return []
    with open(queue_csv, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return []
    # The queue's symbol column is "symbol"; fall back to the first column.
    key = "symbol" if "symbol" in rows[0] else next(iter(rows[0]))
    return [r[key].strip() for r in rows if r.get(key, "").strip()]


def _report_dates(reports_dir: Path) -> dict[str, str]:
    """Map ticker -> screen_date for every report on disk."""
    dates: dict[str, str] = {}
    for path in reports_dir.glob("*.json"):
        try:
            with open(path) as f:
                screen_date = json.load(f).get("screen_date", "")
        except (json.JSONDecodeError, OSError):
            screen_date = ""
        dates[path.stem] = screen_date or _EPOCH
    return dates


def select_batch(
    reports_dir: Path = DEFAULT_REPORTS,
    queue_csv: Path = DEFAULT_QUEUE,
    count: int = DEFAULT_COUNT,
) -> tuple[str, list[str]]:
    """Return ``(mode, tickers)`` for the next screening batch."""
    queue = _load_queue(queue_csv)
    report_dates = _report_dates(reports_dir)
    screened = set(report_dates)

    remaining = [t for t in queue if t not in screened]
    if remaining:
        return "NEW", remaining[:count]

    # REFRESH: rank the FULL report set, oldest screen_date first (ties broken
    # by ticker for deterministic, reproducible batches).
    ranked = sorted(report_dates.items(), key=lambda kv: (kv[1], kv[0]))
    return "REFRESH", [ticker for ticker, _ in ranked[:count]]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Select the next batch of tickers to screen."
    )
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--reports", type=Path, default=DEFAULT_REPORTS)
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument(
        "--json", action="store_true", help='emit {"mode": ..., "tickers": [...]}'
    )
    args = parser.parse_args()

    mode, tickers = select_batch(args.reports, args.queue, args.count)
    if args.json:
        print(json.dumps({"mode": mode, "tickers": tickers}))
    else:
        print(f"MODE: {mode}")
        print(f"COUNT: {len(tickers)}")
        print(" ".join(tickers))


if __name__ == "__main__":
    main()
