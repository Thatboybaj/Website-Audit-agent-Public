"""AEO audit: is this site ready to be found, understood and cited by AI answer engines?"""
from __future__ import annotations

from dataclasses import asdict

from .. import scoring
from ..crawler import SiteData
from . import checks, fixes
from .bots import ROLE_LABEL


def run(site: SiteData) -> dict:
    areas, ctx = checks.run_all(site)
    for a in areas:
        a.compute_score()
    score = scoring.overall(areas)
    ld = ctx["jsonld"]
    brand = (site.ai.get("aeo") or {}).get("brand") or fixes.brand_name(site, ld)
    bots = next((c.data.get("bots") for c in areas[0].checks if c.id == "ai_search_bots"), [])
    for b in bots:
        b["role_label"] = ROLE_LABEL[b["role"]]
    return {
        "score": score,
        "band": scoring.band(score),
        "brand": brand,
        "areas": [asdict(a) for a in areas],
        "bots": bots,
        "schema_types": ctx["jsonld_types"],
        "questions_found": ctx["questions"],
        "ai": {k: v for k, v in (site.ai.get("aeo") or {}).items() if k in ("ai_description", "missing", "buyer_questions", "clarity", "brand")},
        "fixes": fixes.build(site, brand, ld, ctx["questions"], site.ai.get("aeo")),
        "visibility": None,
    }
