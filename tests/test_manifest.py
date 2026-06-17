"""Tests for the Dashboard manifest builder (main._build_manifest)."""

import json
from datetime import date

from main import _build_manifest
from scripts.verify_manifest import verify

REQUIRED_KEYS = {
    "ticker",
    "name",
    "sleeve",
    "recommendation",
    "overall_score",
    "screen_date",
}


def test_manifest_is_array_with_required_keys():
    reports = [
        {
            "ticker": "AAA",
            "name": "Alpha Corp",
            "sleeve": "Growth",
            "recommendation": "BUY",
            "overall_score": 81,
            "screen_date": "2026-06-17",
        }
    ]

    manifest = _build_manifest(reports)

    assert isinstance(manifest, list)
    assert REQUIRED_KEYS <= manifest[0].keys()
    assert manifest[0]["screen_date"] == "2026-06-17"


def test_manifest_screen_date_is_rederived_from_reports():
    """A fresh run's manifest must reflect today's screen_date, never a stale one."""
    today = date.today().isoformat()
    reports = [
        {"ticker": "OLD", "name": "Old", "screen_date": "2026-04-01"},
        {"ticker": "NEW", "name": "New", "screen_date": today},
    ]

    manifest = _build_manifest(reports)

    newest = max(entry["screen_date"] for entry in manifest)
    assert newest == today


def test_verify_detects_drift(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "AAA.json").write_text(
        json.dumps({"ticker": "AAA", "name": "A", "screen_date": "2026-06-17"})
    )
    manifest_path = tmp_path / "manifest.json"
    # Stale manifest: screen_date lags the report file.
    manifest_path.write_text(
        json.dumps(
            [
                {
                    "ticker": "AAA",
                    "name": "A",
                    "sleeve": "",
                    "recommendation": "",
                    "overall_score": 0,
                    "screen_date": "2026-06-01",
                }
            ]
        )
    )

    errors = verify(manifest_path, reports_dir)

    assert any("screen_date" in e for e in errors)


def test_verify_passes_when_consistent(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    report = {
        "ticker": "AAA",
        "name": "Alpha",
        "sleeve": "Growth",
        "recommendation": "BUY",
        "overall_score": 81,
        "screen_date": "2026-06-17",
    }
    (reports_dir / "AAA.json").write_text(json.dumps(report))
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_build_manifest([report])))

    assert verify(manifest_path, reports_dir) == []
