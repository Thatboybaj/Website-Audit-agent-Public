"""Core data models for the audit agent."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional

STATUS_SCORE = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
IMPACT_WEIGHT = {"high": 3, "medium": 2, "low": 1}
EFFORT_WEIGHT = {"easy": 1, "medium": 2, "hard": 3}


@dataclass
class Check:
    id: str
    label: str                     # mirrors a cheat-sheet line item
    status: str                    # pass | warn | fail | info | skip
    detail: str
    fix: str = ""
    impact: str = "medium"         # high | medium | low
    effort: str = "easy"           # easy | medium | hard
    pages: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def scored(self) -> bool:
        return self.status in STATUS_SCORE


@dataclass
class AreaResult:
    number: int
    key: str
    name: str
    checks: list[Check]
    key_metric_label: str
    key_metric_value: str = ""
    score: int = 0
    weight: int = 10

    def compute_score(self) -> int:
        scored = [c for c in self.checks if c.scored]
        if not scored:
            self.score = 0
            return 0
        total_w = sum(IMPACT_WEIGHT[c.impact] for c in scored)
        got = sum(IMPACT_WEIGHT[c.impact] * STATUS_SCORE[c.status] for c in scored)
        self.score = round(100 * got / total_w)
        return self.score


@dataclass
class AuditReport:
    url: str
    audited_at: str
    pages_crawled: int
    overall_score: int
    band: dict
    areas: list[AreaResult]
    action_plan: dict
    quick_wins: list[dict]
    summary: str
    outreach_email: str = ""
    comparison: Optional[dict] = None
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)
