"""Claude layer (optional): content evaluation, executive summary, outreach email.
Set ANTHROPIC_API_KEY to enable. Without it the agent uses deterministic fallbacks."""
from __future__ import annotations

import json
import os
import re

MODEL = os.getenv("AUDIT_MODEL", "claude-sonnet-5-5")


def enabled() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


async def _ask(prompt: str, max_tokens: int = 900) -> str:
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic()
    msg = await client.messages.create(model=MODEL, max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


async def evaluate_content(url: str, title: str, h1: str, text: str) -> dict:
    if not enabled() or len(text.split()) < 40:
        return {}
    prompt = f"""You are a conversion copywriter auditing a website homepage.
URL: {url}
Title: {title}
H1: {h1}
Body copy (truncated):
\"\"\"{text[:6000]}\"\"\"

Rate the copy and return ONLY JSON:
{{"audience": "<who this site is for, 1 short phrase>",
 "relevance": <0-10: does copy speak to that audience's problems/outcomes>,
 "relevance_note": "<1 sentence>", "relevance_fix": "<1 concrete rewrite suggestion>",
 "clarity": <0-10: is it immediately clear what they offer, for whom, and the next step>,
 "clarity_note": "<1 sentence>", "clarity_fix": "<1 concrete suggestion>"}}"""
    try:
        raw = await _ask(prompt, 500)
        return json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
    except Exception as e:
        return {"error": str(e)}


def _fallback_summary(report: dict) -> str:
    worst = sorted(report["areas"], key=lambda a: a["score"])[:3]
    best = sorted(report["areas"], key=lambda a: -a["score"])[:2]
    top = report["action_plan"]["prioritize"][:3]
    fmt = lambda xs: ", ".join("%s (%s)" % (a["name"], a["score"]) for a in xs)
    first = "; ".join("%s — %s" % (i["check"], i["fix"]) for i in top)
    return (f"{report['url']} scores {report['overall_score']}/100 ({report['band']['label']}). "
            f"Strongest areas: {fmt(best)}. Weakest: {fmt(worst)}. Start with: {first}")


async def summarize(report: dict) -> str:
    if not enabled():
        return _fallback_summary(report)
    slim = {"url": report["url"], "score": report["overall_score"], "band": report["band"]["label"],
            "areas": [{"name": a["name"], "score": a["score"], "metric": f"{a['key_metric_label']}: {a['key_metric_value']}"} for a in report["areas"]],
            "top_issues": [{k: i[k] for k in ("area", "check", "status", "detail", "fix")} for i in report["action_plan"]["prioritize"]]}
    prompt = f"""Write a website audit executive summary for a business owner (not a developer).
Data: {json.dumps(slim)}
Format: 1 short paragraph on overall health and what it means for traffic/leads, then 3 bullet points
'Fix first' with the business impact of each. Plain language, no jargon, max 150 words. No headings."""
    try:
        return await _ask(prompt, 400)
    except Exception:
        return _fallback_summary(report)


def _fallback_email(report: dict, sender: str) -> str:
    top = report["action_plan"]["prioritize"][:3]
    lines = "\n".join(f"• {i['check']}: {i['detail']}" for i in top)
    return (f"Subject: Quick audit of {report['url']} — {report['overall_score']}/100\n\n"
            f"Hi there,\n\nI ran a quick audit of {report['url']} and it scored {report['overall_score']}/100 "
            f"({report['band']['label'].lower()}). Three things stood out that are likely costing you visitors and leads:\n\n"
            f"{lines}\n\nAll three are fixable in a few days. Happy to send the full report or walk you through it on a 15-minute call.\n\n"
            f"Best,\n{sender}")


async def outreach_email(report: dict, sender: str = "Bright") -> str:
    """Cold-outreach email built from the audit — plugs into the lead agent."""
    if not enabled():
        return _fallback_email(report, sender)
    top = [{k: i[k] for k in ("check", "detail", "fix")} for i in report["action_plan"]["prioritize"][:3]]
    prompt = f"""Write a short cold email from {sender}, a freelance web designer/developer (Framer & Webflow),
to the owner of {report['url']}. Their site audit scored {report['overall_score']}/100. Top issues: {json.dumps(top)}.
Rules: subject line first ("Subject: ..."), under 120 words, specific to the issues, one business-impact sentence,
soft CTA offering the full report or a 15-min call. No hype, no fake compliments, no placeholders."""
    try:
        return await _ask(prompt, 400)
    except Exception:
        return _fallback_email(report, sender)
