"""Shared helpers for checks."""
from __future__ import annotations

import re
from typing import Optional

from ..crawler import SiteData

CTA_RE = re.compile(r"\b(get|start|book|contact|buy|try|sign ?up|schedule|request|download|shop|join|subscribe|hire|quote|demo|call|order|apply|register|let'?s talk|work with|enquire|inquire)\b", re.I)


def ratio_status(ok: int, total: int, good: float = 0.95, fair: float = 0.7) -> str:
    if total == 0:
        return "pass"
    r = ok / total
    return "pass" if r >= good else "warn" if r >= fair else "fail"


def threshold(value: float, good: float, fair: float, higher_better: bool = True) -> str:
    if higher_better:
        return "pass" if value >= good else "warn" if value >= fair else "fail"
    return "pass" if value <= good else "warn" if value <= fair else "fail"


def sample(items, n: int = 5) -> list:
    return list(items)[:n]


def short(url: str, site: SiteData) -> str:
    return url.replace(site.origin, "") or "/"


def psi_audit(site: SiteData, audit_id: str, strategy: str = "mobile") -> Optional[dict]:
    return (site.psi.get(strategy) or {}).get("audits", {}).get(audit_id)


def psi_cat(site: SiteData, cat: str, strategy: str = "mobile") -> Optional[int]:
    return (site.psi.get(strategy) or {}).get("categories", {}).get(cat)


def bm(site: SiteData, viewport: str = "mobile") -> Optional[dict]:
    v = site.browser.get(viewport)
    return v if isinstance(v, dict) and "viewport" in v else None


def all_html(site: SiteData) -> str:
    return "\n".join(p.html for p in site.html_pages)


def syllables(word: str) -> int:
    word = word.lower()
    groups = re.findall(r"[aeiouy]+", word)
    n = len(groups) - (1 if word.endswith("e") and len(groups) > 1 else 0)
    return max(1, n)


def flesch(text: str) -> Optional[float]:
    sentences = [s for s in re.split(r"[.!?]+\s", text) if len(s.split()) > 2]
    words = re.findall(r"[A-Za-z]+", text)
    if len(words) < 50 or not sentences:
        return None
    syl = sum(syllables(w) for w in words)
    return round(206.835 - 1.015 * (len(words) / len(sentences)) - 84.6 * (syl / len(words)), 1)


def main_text(page) -> str:
    """Body text without nav/header/footer boilerplate."""
    from bs4 import BeautifulSoup
    if not page.soup:
        return ""
    s = BeautifulSoup(str(page.soup.body or page.soup), "lxml")
    for t in s(["script", "style", "noscript", "nav", "header", "footer", "svg", "form"]):
        t.decompose()
    return re.sub(r"\s+", " ", s.get_text(" ")).strip()
