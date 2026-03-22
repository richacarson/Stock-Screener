"""Patch all existing reports with correct Inspire Insight scores from CSV.

Fixes faith_alignment section with actual scores and attributions from
data/inspire_insight_scores.csv. Recalculates overall_score and updates
recommendation if the score band changed.
"""

import csv
import json
import os
import sys

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
INSPIRE_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "inspire_insight_scores.csv")


def load_inspire_data() -> dict[str, dict]:
    """Load inspire scores CSV into a ticker-keyed dict."""
    data = {}
    with open(INSPIRE_CSV, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row["ticker"].strip()
            score_str = row["score"].strip()

            if score_str in ("N/A", ""):
                score = None
            else:
                score = int(score_str)

            neg_attrs = [
                a.strip()
                for a in row["negative_attributions"].split("|")
                if a.strip()
            ]
            pos_attrs = [
                a.strip()
                for a in row["positive_attributions"].split("|")
                if a.strip()
            ]

            data[ticker] = {
                "score": score,
                "negative_attributions": neg_attrs,
                "positive_attributions": pos_attrs,
            }
    return data


def get_label(score: int | None) -> str:
    """Map inspire score to label."""
    if score is None:
        return "PENDING"
    if score > 25:
        return "ALIGNED"
    if score < -25:
        return "MISALIGNED"
    return "MIXED"


def calculate_overall(report: dict) -> int:
    """Recalculate overall score using CLAUDE.md formula.

    5 dimensions at 20% each. If no dividend, 4 dimensions at 25% each.
    """
    ee = report["excellence_evaluation"]
    inn = ee["innovation"]["score"]
    insp = ee["inspiration"]["score"]
    infra = ee["infrastructure"]["score"]
    ai = report["ai_resilience"]["score"]
    ig = report["infinite_game"]["overall"]
    faith_score = report["faith_alignment"]["inspire_impact_score"]

    ds_obj = report["income_quality"]["dividend_safety"]
    has_dividend = ds_obj is not None and isinstance(ds_obj, dict)

    excellence = (inn + insp + infra) / 3 / 10 * 20
    ai_dim = ai / 10 * 20
    ig_dim = ig / 10 * 20

    if faith_score is not None:
        faith_dim = (faith_score + 100) / 200 * 20
    else:
        faith_dim = 10.0  # neutral default for pending scores

    if has_dividend:
        ds = ds_obj["score"]
        income_dim = ds / 10 * 20
        overall = excellence + ai_dim + ig_dim + income_dim + faith_dim
    else:
        # 4 dimensions at 25% each (scale up from 80% to 100%)
        overall = (excellence + ai_dim + ig_dim + faith_dim) * 100 / 80

    return round(overall)


def get_recommendation(score: int) -> str:
    """Map overall score to recommendation."""
    if score >= 80:
        return "BUY"
    if score >= 60:
        return "HOLD"
    if score >= 40:
        return "WATCH"
    return "SELL"


def patch_reports():
    """Patch all reports with correct inspire data."""
    inspire_data = load_inspire_data()
    print(f"Loaded {len(inspire_data)} inspire scores")

    report_files = sorted(
        f for f in os.listdir(REPORTS_DIR) if f.endswith(".json")
    )
    print(f"Found {len(report_files)} reports to patch")

    patched = 0
    score_changed = 0
    rec_changed = 0

    for fname in report_files:
        ticker = fname.replace(".json", "")
        filepath = os.path.join(REPORTS_DIR, fname)

        with open(filepath) as f:
            report = json.load(f)

        inspire = inspire_data.get(ticker)
        if not inspire:
            print(f"  WARNING: {ticker} not found in inspire CSV, skipping")
            continue

        old_faith = report.get("faith_alignment", {})
        old_inspire_score = old_faith.get("inspire_impact_score")

        # Build new faith_alignment
        new_faith = {
            "inspire_impact_score": inspire["score"],
            "label": get_label(inspire["score"]),
            "negative_attributions": inspire["negative_attributions"],
            "positive_attributions": inspire["positive_attributions"],
            "source": "Inspire Insight",
        }
        report["faith_alignment"] = new_faith

        # Recalculate overall score
        old_overall = report["overall_score"]
        new_overall = calculate_overall(report)
        report["overall_score"] = new_overall

        if old_overall != new_overall:
            score_changed += 1

        # Update recommendation if band changed
        old_rec = report["recommendation"]
        new_rec = get_recommendation(new_overall)
        report["recommendation"] = new_rec

        if old_rec != new_rec:
            rec_changed += 1
            print(f"  {ticker}: rec changed {old_rec} -> {new_rec} (score {old_overall} -> {new_overall})")

        # Write back
        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)
            f.write("\n")

        patched += 1

    print(f"\nPatched {patched} reports")
    print(f"  Score changed: {score_changed}")
    print(f"  Recommendation changed: {rec_changed}")


if __name__ == "__main__":
    patch_reports()
