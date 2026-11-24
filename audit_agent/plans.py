"""Plans & entitlements. Free = full SEO audit, AEO locked (nothing from it is sent). Pro = full AEO, AI visibility, fixes, white-label.
No payment provider yet: Pro is unlocked with access codes (PRO_CODES). When payments arrive, the checkout
webhook only needs to issue a code (or set a plan on a user) — nothing else changes."""
from __future__ import annotations

import copy
import os
import time

PLANS = {
    "free": {"label": "Free", "max_pages": 5, "aeo_full": False, "visibility": False, "ai": False,
             "white_label": False, "compare": False, "email": False, "fixes": False},
    "pro": {"label": "AEO unlocked", "max_pages": 25, "aeo_full": True, "visibility": True, "ai": True,
            "white_label": True, "compare": True, "email": True, "fixes": True},
    "owner": {"label": "Owner", "max_pages": 50, "aeo_full": True, "visibility": True, "ai": True,
              "white_label": True, "compare": True, "email": True, "fixes": True},
}


def pricing() -> dict:
    return {
        "currency_note": os.getenv("PRICE_NOTE", "Launch pricing"),
        "aeo_report": os.getenv("AEO_REPORT_PRICE", "$29"),
        "pro_monthly": os.getenv("PRO_MONTHLY_PRICE", "$49/mo"),
        "checkout_url": os.getenv("CHECKOUT_URL", ""),          # empty = "Request access" flow
        "free_features": ["Full SEO audit — 10 areas, 70+ checks", "Health score + action plan", "PDF & HTML report",
                          "AI Search Readiness score (teaser)", f"{PLANS['free']['max_pages']} pages per audit"],
        "pro_features": ["Everything in Free", "Full AEO audit — 9 categories, 40+ checks", "AI crawler access + firewall test",
                         "AI answer visibility test (Claude / Perplexity)", "Ready-to-paste fixes: llms.txt, schema, robots.txt",
                         "AI-written summary & outreach email", "Competitor comparison", "White-label PDF reports",
                         f"Up to {PLANS['pro']['max_pages']} pages per audit"],
    }


def pro_codes() -> set[str]:
    return {c.strip() for c in os.getenv("PRO_CODES", "").split(",") if c.strip()}


def resolve(authorization: str | None, pro_code: str | None) -> str:
    token = os.getenv("AUDIT_API_TOKEN")
    if token and authorization == f"Bearer {token}":
        return "owner"
    if pro_code and pro_code.strip() in pro_codes():
        return "pro"
    return "free"


# --- usage limits (in-memory: best effort on serverless; move to a DB/Redis when you add accounts)
_usage: dict[str, list[float]] = {}


def over_limit(key: str, limit: int, window: int) -> bool:
    now = time.time()
    hits = [t for t in _usage.get(key, []) if now - t < window]
    if len(hits) >= limit:
        _usage[key] = hits
        return True
    _usage[key] = hits + [now]
    return False


LOCK_NOTE = "Unlock the AEO audit to see what's wrong and how to fix it."


def redact(report: dict, plan: str) -> dict:
    """Remove paid detail on the server so it never reaches a free user's browser."""
    r = copy.deepcopy(report)
    r["plan"] = plan
    ent = PLANS[plan]
    if not ent["email"]:
        r["outreach_email"] = ""
    a = r.get("aeo")
    if a and not a.get("error") and not ent["aeo_full"]:
        # Locked: the AEO audit ran (so unlocking is instant to explain), but nothing from it leaves the server.
        hidden = sum(c["status"] in ("warn", "fail") for area in a.get("areas", []) for c in area.get("checks", []))
        r["aeo"] = {"locked": True, "issues_hidden": hidden, "brand": a.get("brand", "")}
    return r
