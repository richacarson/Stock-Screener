#!/usr/bin/env python3
"""Fail if output/manifest.json drifts from the source report files.

The Dashboard renders its whole stock list from the published manifest.json, so
the manifest must always be re-derived from reports/*.json. This guards the
deploy against the regression where an incremental deploy clobbered manifest.json
with a stale rebuild, leaving screen_dates lagging behind the report files.

Run after `python main.py` (which writes output/manifest.json). Exit non-zero
on any drift so a CI deploy stops instead of publishing a stale manifest.
"""

import json
import sys
from pathlib import Path

REQUIRED_KEYS = {
    "ticker",
    "name",
    "sleeve",
    "recommendation",
    "overall_score",
    "screen_date",
}


def verify(
    manifest_path: Path = Path("output/manifest.json"),
    reports_dir: Path = Path("reports"),
) -> list[str]:
    """Return a list of drift errors (empty means the manifest is consistent)."""
    errors: list[str] = []

    if not manifest_path.exists():
        return [f"{manifest_path} not found — run main.py first."]

    manifest = json.loads(manifest_path.read_text())
    if not isinstance(manifest, list):
        return ["manifest.json must be a JSON array of report stubs."]

    by_ticker: dict[str, dict] = {}
    for entry in manifest:
        missing = REQUIRED_KEYS - entry.keys()
        if missing:
            errors.append(f"{entry.get('ticker', '?')}: missing keys {sorted(missing)}")
        by_ticker[entry.get("ticker")] = entry

    for path in sorted(reports_dir.glob("*.json")):
        ticker = path.stem
        try:
            report = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"{ticker}: unreadable report ({exc})")
            continue
        entry = by_ticker.get(ticker)
        if entry is None:
            errors.append(f"{ticker}: report has no manifest entry")
            continue
        if entry.get("screen_date") != report.get("screen_date"):
            errors.append(
                f"{ticker}: manifest screen_date {entry.get('screen_date')!r} "
                f"!= report {report.get('screen_date')!r}"
            )

    return errors


def main() -> int:
    errors = verify()
    if errors:
        print(f"Manifest verification FAILED ({len(errors)} issues):")
        for err in errors[:50]:
            print(f"  - {err}")
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more")
        return 1
    manifest = json.loads(Path("output/manifest.json").read_text())
    newest = max((e["screen_date"] for e in manifest), default="n/a")
    print(
        f"Manifest OK — {len(manifest)} entries match reports/*.json "
        f"(newest screen_date: {newest})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
