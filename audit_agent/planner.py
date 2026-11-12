"""Audit Action Plan: Prioritize → Fix & Optimize → Test & Monitor → Re-audit, plus Quick Wins."""
from .models import AreaResult, IMPACT_WEIGHT, EFFORT_WEIGHT

QUICK_WIN_MAP = {  # cheat-sheet quick wins -> check ids
    "Improve page speed": ["page_speed", "caching", "minify", "server_response", "page_weight"],
    "Fix broken links & 404s": ["broken_links", "redirect_chains"],
    "Optimize images": ["image_optimization", "image_alt", "alt_text"],
    "Update titles & meta descriptions": ["title_tags", "meta_descriptions"],
    "Check mobile usability": ["mobile_friendly", "viewport", "tap_targets", "horizontal_scroll", "text_readability"],
}


def priority(c) -> float:
    sev = 1.0 if c.status == "fail" else 0.5
    return IMPACT_WEIGHT[c.impact] * sev * 10 / EFFORT_WEIGHT[c.effort]


def issues(areas: list[AreaResult]) -> list[dict]:
    out = []
    for a in areas:
        for c in a.checks:
            if c.status in ("fail", "warn"):
                out.append({"area": a.name, "area_key": a.key, "check": c.label, "check_id": c.id, "status": c.status,
                            "impact": c.impact, "effort": c.effort, "detail": c.detail, "fix": c.fix,
                            "priority": round(priority(c), 1), "examples": c.pages[:5]})
    return sorted(out, key=lambda i: -i["priority"])


def quick_wins(areas: list[AreaResult]) -> list[dict]:
    by_id = {c.id: (a, c) for a in areas for c in a.checks}
    wins = []
    for title, ids in QUICK_WIN_MAP.items():
        hits = [by_id[i] for i in ids if i in by_id and by_id[i][1].status in ("fail", "warn")]
        wins.append({"title": title, "status": "todo" if hits else "done",
                     "items": [f"{c.label}: {c.fix or c.detail}" for _, c in hits][:3]})
    return wins


def cadence(score: int) -> str:
    return "monthly" if score < 50 else "every 2 months" if score < 80 else "quarterly"


def build(areas: list[AreaResult], score: int) -> dict:
    iss = issues(areas)
    critical = [i for i in iss if i["status"] == "fail" and i["impact"] == "high"]
    easy_high = [i for i in iss if i["effort"] == "easy" and i["impact"] in ("high", "medium")]
    top = (critical + [i for i in easy_high if i not in critical])[:7] or iss[:7]
    grouped = {}
    for i in iss:
        grouped.setdefault(i["area"], []).append(i)
    return {
        "prioritize": top,
        "fix_and_optimize": grouped,
        "test_and_monitor": [{"area": a.name, "metric": a.key_metric_label, "baseline": a.key_metric_value} for a in areas],
        "re_audit": {"cadence": cadence(score),
                     "note": f"Re-run the audit {cadence(score)} and compare with --compare <previous.json> to track progress."},
        "counts": {"critical": len([i for i in iss if i["status"] == "fail"]), "warnings": len([i for i in iss if i["status"] == "warn"]),
                   "passed": sum(1 for a in areas for c in a.checks if c.status == "pass")},
    }


def compare(current: dict, previous: dict) -> dict:
    prev = {a["key"]: a["score"] for a in previous.get("areas", [])}
    return {
        "previous_date": previous.get("audited_at"),
        "mode_changed": any(current["meta"].get(k) != previous.get("meta", {}).get(k) for k in ("psi", "browser")),
        "overall_delta": current["overall_score"] - previous.get("overall_score", 0),
        "previous_overall": previous.get("overall_score"),
        "areas": {a["key"]: {"now": a["score"], "before": prev.get(a["key"]), "delta": a["score"] - prev.get(a["key"], a["score"])}
                  for a in current["areas"]},
    }
