"""Google PageSpeed Insights (Lighthouse) integration. Works without a key at low volume;
set PSI_API_KEY for reliable use (free from Google Cloud console)."""
from __future__ import annotations

import asyncio
import os

import httpx

ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
CATEGORIES = ["performance", "accessibility", "seo", "best-practices"]
AUDITS = [
    "largest-contentful-paint", "cumulative-layout-shift", "total-blocking-time", "first-contentful-paint",
    "speed-index", "server-response-time", "uses-optimized-images", "modern-image-formats", "uses-responsive-images",
    "offscreen-images", "unminified-css", "unminified-javascript", "unused-javascript", "uses-long-cache-ttl",
    "uses-text-compression", "viewport", "tap-targets", "font-size", "content-width", "color-contrast",
    "render-blocking-resources", "total-byte-weight",
]


async def run_psi(url: str, strategy: str, key: str | None) -> dict:
    params = [("url", url), ("strategy", strategy)] + [("category", c) for c in CATEGORIES]
    if key:
        params.append(("key", key))
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.get(ENDPOINT, params=params)
        r.raise_for_status()
        data = r.json()
    lh = data.get("lighthouseResult", {})
    cats = {k: round((v.get("score") or 0) * 100) for k, v in lh.get("categories", {}).items()}
    audits = {}
    for a in AUDITS:
        if a in lh.get("audits", {}):
            au = lh["audits"][a]
            audits[a] = {"score": au.get("score"), "value": au.get("numericValue"), "display": au.get("displayValue", "")}
    field = {}
    for k, v in (data.get("loadingExperience", {}).get("metrics") or {}).items():
        field[k] = {"p75": v.get("percentile"), "category": v.get("category")}
    return {"categories": cats, "audits": audits, "field": field}


async def run_all(url: str, enabled: bool = True) -> dict:
    if not enabled:
        return {}
    key = os.getenv("PSI_API_KEY")
    out = {}
    results = await asyncio.gather(*(run_psi(url, s, key) for s in ("mobile", "desktop")), return_exceptions=True)
    for strat, res in zip(("mobile", "desktop"), results):
        if isinstance(res, Exception):
            out.setdefault("errors", []).append(f"PSI {strat}: {type(res).__name__}: {res}")
        else:
            out[strat] = res
    return out
