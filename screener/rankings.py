"""Stock ranking — orders reports by overall IOWN score.

In the static JSON architecture, Claude Code generates the scores
and stores them in reports/*.json. This module simply sorts them.
"""


def rank_reports(reports: list[dict]) -> list[dict]:
    """Sort reports by overall_score descending."""
    return sorted(reports, key=lambda r: r.get("overall_score", 0), reverse=True)
