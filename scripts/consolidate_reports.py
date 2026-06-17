#!/usr/bin/env python3
"""One-time consolidation of orphaned daily-screening branches.

Each scheduled screening run historically pushed a throwaway
`claude/daily-screening-YYYY-MM-DD` branch that was never merged back, so the
freshest version of any given report is scattered across ~76 branches while the
default branch stayed frozen. This script reconstructs the freshest state:

  for each ticker, pick the report with the newest screen_date across the
  current working tree (HEAD) and every daily-screening branch, and write that
  version into reports/.

It reads blobs with `git cat-file --batch` (deduplicated by blob SHA, so the
work is proportional to the number of *distinct* report versions, not
branches x files). Nothing is committed — run it, review the diff, then commit.
"""

from __future__ import annotations

import io
import json
import subprocess
from collections import defaultdict
from pathlib import Path

REPORTS_DIR = Path("reports")
_EPOCH = "0000-00-00"


def _run(args: list[str]) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout


def _screening_refs() -> list[str]:
    out = _run(["git", "branch", "-r", "--format=%(refname:short)"])
    refs = [
        line.strip()
        for line in out.splitlines()
        if "origin/claude/daily-screening-" in line
    ]
    refs.append("HEAD")  # include the current working branch
    return refs


def _ticker_blobs(refs: list[str]) -> dict[str, set[str]]:
    """Map ticker -> set of candidate blob SHAs across all refs."""
    ticker_blobs: dict[str, set[str]] = defaultdict(set)
    for ref in refs:
        out = _run(["git", "ls-tree", "-r", ref, "reports/"])
        for line in out.splitlines():
            meta, _, path = line.partition("\t")
            parts = meta.split()
            if len(parts) < 3 or parts[1] != "blob":
                continue
            if not path.endswith(".json"):
                continue
            ticker = Path(path).stem
            ticker_blobs[ticker].add(parts[2])
    return ticker_blobs


def _blob_screen_dates(shas: list[str]) -> dict[str, tuple[str, bytes]]:
    """Batch-read blobs; return sha -> (screen_date, raw content)."""
    proc = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    out, _ = proc.communicate(("\n".join(shas) + "\n").encode())
    buf = io.BytesIO(out)
    result: dict[str, tuple[str, bytes]] = {}
    while True:
        header = buf.readline()
        if not header:
            break
        parts = header.split()
        if len(parts) < 3:  # e.g. "<sha> missing"
            continue
        sha, _typ, size = parts[0].decode(), parts[1], int(parts[2])
        content = buf.read(size)
        buf.read(1)  # trailing newline
        try:
            screen_date = json.loads(content).get("screen_date") or _EPOCH
        except (json.JSONDecodeError, ValueError):
            screen_date = _EPOCH
        result[sha] = (screen_date, content)
    return result


def consolidate() -> dict[str, int]:
    refs = _screening_refs()
    print(f"Scanning {len(refs)} refs ({len(refs) - 1} screening branches + HEAD)...")

    ticker_blobs = _ticker_blobs(refs)
    unique = sorted({sha for shas in ticker_blobs.values() for sha in shas})
    print(f"{len(ticker_blobs)} tickers, {len(unique)} unique report versions")

    blob_data = _blob_screen_dates(unique)

    written = 0
    unchanged = 0
    for ticker, shas in sorted(ticker_blobs.items()):
        # pick the freshest version; tie-break by sha for determinism
        best_sha = max(shas, key=lambda s: (blob_data[s][0], s))
        best_date, content = blob_data[best_sha]
        dest = REPORTS_DIR / f"{ticker}.json"
        current = dest.read_bytes() if dest.exists() else b""
        if current == content:
            unchanged += 1
            continue
        dest.write_bytes(content)
        written += 1

    print(f"Updated {written} reports, {unchanged} already current.")
    return {"tickers": len(ticker_blobs), "written": written, "unchanged": unchanged}


if __name__ == "__main__":
    consolidate()
