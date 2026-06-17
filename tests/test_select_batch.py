"""Tests for the daily-screening batch selector (scripts/select_batch.py)."""

import csv
import json
from pathlib import Path

from scripts.select_batch import select_batch


def _write_report(reports_dir: Path, ticker: str, screen_date: str) -> None:
    (reports_dir / f"{ticker}.json").write_text(
        json.dumps({"ticker": ticker, "screen_date": screen_date})
    )


def _write_queue(path: Path, rows: list[tuple[str, int]]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["symbol", "avg_daily_volume"])
        writer.writerows(rows)


def test_new_mode_returns_unscreened_queue_in_order(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    queue = tmp_path / "queue.csv"
    _write_queue(queue, [("AAA", 900), ("BBB", 800), ("CCC", 700)])
    _write_report(reports, "AAA", "2026-01-01")  # already screened

    mode, batch = select_batch(reports, queue, count=10)

    assert mode == "NEW"
    assert batch == ["BBB", "CCC"]  # queue order, screened AAA skipped


def test_new_mode_respects_count(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    queue = tmp_path / "queue.csv"
    _write_queue(queue, [("AAA", 900), ("BBB", 800), ("CCC", 700)])

    mode, batch = select_batch(reports, queue, count=2)

    assert mode == "NEW"
    assert batch == ["AAA", "BBB"]


def test_refresh_includes_tickers_not_in_queue(tmp_path):
    """Regression: seed tickers never in the queue must still rotate.

    This is the NVDA/TSM/AMD/QCOM bug — they were screened before the queue was
    built, so they are absent from screening_queue.csv and the old logic skipped
    them forever.
    """
    reports = tmp_path / "reports"
    reports.mkdir()
    queue = tmp_path / "queue.csv"
    _write_queue(queue, [("AAA", 900)])
    _write_report(reports, "AAA", "2026-06-01")
    _write_report(reports, "NVDA", "2026-04-01")  # not in queue, oldest

    mode, batch = select_batch(reports, queue, count=10)

    assert mode == "REFRESH"  # queue fully screened
    assert "NVDA" in batch
    assert batch[0] == "NVDA"  # oldest screen_date first


def test_refresh_orders_by_oldest_screen_date(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    queue = tmp_path / "queue.csv"
    _write_queue(queue, [("AAA", 900)])
    _write_report(reports, "AAA", "2026-05-01")
    _write_report(reports, "BBB", "2026-03-01")
    _write_report(reports, "CCC", "2026-04-01")

    mode, batch = select_batch(reports, queue, count=2)

    assert mode == "REFRESH"
    assert batch == ["BBB", "CCC"]  # oldest two, oldest first


def test_missing_screen_date_sorts_first(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    queue = tmp_path / "queue.csv"
    _write_queue(queue, [("AAA", 900)])
    _write_report(reports, "AAA", "2026-05-01")
    (reports / "NODATE.json").write_text(json.dumps({"ticker": "NODATE"}))

    mode, batch = select_batch(reports, queue, count=1)

    assert mode == "REFRESH"
    assert batch == ["NODATE"]


def test_empty_queue_falls_back_to_refresh(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    queue = tmp_path / "queue.csv"  # does not exist
    _write_report(reports, "AAA", "2026-05-01")

    mode, batch = select_batch(reports, queue, count=10)

    assert mode == "REFRESH"
    assert batch == ["AAA"]
