"""Audit scoring guide + overall health score."""
from .models import AreaResult

BANDS = [
    (90, "Excellent", "Your site is healthy. Keep optimizing!", "#2e9e44"),
    (70, "Good", "Minor issues found. Easy wins ahead.", "#8cc63f"),
    (50, "Needs Improvement", "Several issues need attention.", "#f5b82e"),
    (30, "Poor", "Major problems affecting performance.", "#f28c28"),
    (0, "Critical", "Immediate action required.", "#e5484d"),
]


def band(score: int) -> dict:
    for floor, label, desc, color in BANDS:
        if score >= floor:
            return {"label": label, "description": desc, "color": color, "range": f"{floor}–{100 if floor == 90 else floor + 19 if floor else 29}"}
    return {}


def overall(areas: list[AreaResult]) -> int:
    scored = [a for a in areas if any(c.scored for c in a.checks)]
    if not scored:
        return 0
    return round(sum(a.score * a.weight for a in scored) / sum(a.weight for a in scored))
