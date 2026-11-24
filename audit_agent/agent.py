"""Orchestrator: crawl → (PSI + browser in parallel) → AI content eval → 10 checks → score → plan → summary."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

from . import ai, browser, psi, planner, scoring, techstack
from . import aeo as aeo_mod
from .checks import AREAS
from .checks._util import main_text
from .crawler import Crawler
from .models import AuditReport


async def run_audit(url: str, max_pages: int = 25, use_psi: bool = True, use_browser: bool = True,
                    use_ai: bool = True, compare_path: Optional[str] = None, sender: str = "Bright",
                    aeo: bool = True, log=print) -> dict:
    crawler = Crawler(url, max_pages=max_pages)
    start = crawler.site.start_url
    log(f"→ Auditing {start}")

    psi_task = asyncio.create_task(psi.run_all(start, use_psi))
    log("  crawling pages, robots, sitemap, links, SSL, headers…")
    site = await crawler.run(aeo=aeo)
    final = site.home.final_url if site.home else start
    log(f"  {len(site.pages)} pages crawled, {len(site.link_status)} links checked")

    if use_browser:
        log("  rendering mobile + desktop in headless browser…")
    site.browser = await browser.render(final, use_browser)
    log("  waiting for PageSpeed Insights…" if use_psi else "  PSI disabled")
    site.psi = await psi_task
    if site.psi.get("errors"):
        site.errors += site.psi["errors"]

    if use_ai and ai.enabled() and site.home and site.home.soup:
        log("  AI evaluating content…")
        s = site.home.soup
        site.ai["content"] = await ai.evaluate_content(final, s.title.string if s.title else "",
                                                       s.find("h1").get_text(" ", strip=True) if s.find("h1") else "",
                                                       main_text(site.home))

    if aeo and use_ai and ai.enabled() and site.home and site.home.soup:
        log("  AI reading the site like an answer engine…")
        s = site.home.soup
        site.ai["aeo"] = await ai.evaluate_aeo(final, s.title.string if s.title else "",
                                               s.find("h1").get_text(" ", strip=True) if s.find("h1") else "",
                                               main_text(site.home))

    areas = []
    for mod in AREAS:
        try:
            a = mod.run(site)
        except Exception as e:  # one broken check never kills the audit
            from .models import AreaResult, Check
            name = mod.__name__.split(".")[-1]
            a = AreaResult(len(areas) + 1, name, name.replace("_", " ").title(),
                           [Check("error", "Check error", "skip", f"{type(e).__name__}: {e}")], "—", "n/a")
        a.compute_score()
        areas.append(a)

    score = scoring.overall(areas)
    report = AuditReport(
        url=final, audited_at=datetime.now(timezone.utc).isoformat(timespec="seconds"), pages_crawled=len(site.pages),
        overall_score=score, band=scoring.band(score), areas=areas, action_plan=planner.build(areas, score),
        quick_wins=planner.quick_wins(areas), summary="",
        meta={"psi": bool(site.psi.get("mobile")), "browser": "mobile" in site.browser, "ai": bool(site.ai.get("content")),
              "ai_content": site.ai.get("content", {}), "errors": site.errors[:20],
              "screenshots": {k: v.get("screenshot") for k, v in site.browser.items() if isinstance(v, dict) and v.get("screenshot")},
              "pages": [page_row(p) for p in site.pages],
              "crawl": {"robots": bool(site.robots_txt), "sitemap": site.sitemap_url, "sitemap_urls": len(site.sitemap_urls),
                        "links_checked": len(site.link_status), "llms_txt": site.llms_txt.get("llms.txt", {}).get("found", False)}},
    ).to_dict()
    report["tech"] = techstack.detect(site)
    report["seo_score"] = score
    if aeo:
        try:
            report["aeo"] = aeo_mod.run(site)
        except Exception as e:
            report["aeo"] = {"error": f"{type(e).__name__}: {e}"}

    if compare_path:
        with open(compare_path) as f:
            report["comparison"] = planner.compare(report, json.load(f))

    log("  writing summary…")
    report["summary"] = await ai.summarize(report) if use_ai else ai._fallback_summary(report)
    report["outreach_email"] = await ai.outreach_email(report, sender) if use_ai else ai._fallback_email(report, sender)
    log(f"✓ Overall health score: {score}/100 ({report['band']['label']})")
    return report


def page_row(p) -> dict:
    row = {"url": p.url, "status": p.status, "words": p.word_count, "ms": p.total_ms, "kb": round(p.size_bytes / 1024)}
    if p.soup:
        t = p.soup.title.string.strip() if p.soup.title and p.soup.title.string else ""
        d = p.soup.find("meta", attrs={"name": "description"})
        dtxt = (d.get("content") or "").strip() if d else ""
        row.update({"title": t[:120], "title_len": len(t), "desc_len": len(dtxt), "desc": dtxt[:200],
                    "h1": len(p.soup.find_all("h1")), "imgs": len(p.soup.find_all("img")),
                    "noalt": len([i for i in p.soup.find_all("img") if not i.has_attr("alt")]),
                    "schema": len(p.soup.find_all("script", type="application/ld+json")),
                    "canonical": bool(p.soup.find("link", rel=lambda v: v and "canonical" in v))})
    return row
