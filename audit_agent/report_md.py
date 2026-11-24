"""JSON + Markdown output (used by both editions)."""
from __future__ import annotations

import copy
import json

ICON = {"pass": "✅", "warn": "⚠️", "fail": "❌", "info": "ℹ️", "skip": "⏭️"}


def to_json(report: dict, include_screenshots: bool = False) -> str:
    r = copy.deepcopy(report)
    if not include_screenshots:
        r.get("meta", {}).pop("screenshots", None)
    return json.dumps(r, indent=2, ensure_ascii=False)


def to_markdown(r: dict) -> str:
    out = [f"# Website Audit — {r['url']}", "",
           f"**Overall health score: {r['overall_score']}/100 — {r['band']['label']}** ({r['band']['description']})  ",
           f"Audited {r['audited_at']} · {r['pages_crawled']} pages crawled · "
           f"PSI {'on' if r['meta']['psi'] else 'off'} · browser {'on' if r['meta']['browser'] else 'off'} · AI {'on' if r['meta']['ai'] else 'off'}", ""]
    if r.get("comparison"):
        c = r["comparison"]
        out += [f"**Change since {c['previous_date']}: {c['overall_delta']:+d} points** (was {c['previous_overall']})" + (" — note: PSI/browser settings differ from the previous run, so some deltas reflect the change in mode." if c.get("mode_changed") else ""), ""]
    out += ["## Summary", "", r["summary"], "", "## Scores by area", "", "| # | Area | Score | Key metric |", "|---|---|---|---|"]
    for a in r["areas"]:
        delta = ""
        if r.get("comparison"):
            d = r["comparison"]["areas"].get(a["key"], {}).get("delta")
            delta = f" ({d:+d})" if d else ""
        out.append(f"| {a['number']} | {a['name']} | {a['score']}{delta} | {a['key_metric_label']}: {a['key_metric_value']} |")
    ap = r["action_plan"]
    out += ["", "## Action plan", "", f"_{ap['counts']['critical']} critical · {ap['counts']['warnings']} warnings · {ap['counts']['passed']} passed_", "",
            "### 1. Prioritize (high impact, easy to fix first)", ""]
    for i, it in enumerate(ap["prioritize"], 1):
        out.append(f"{i}. **{it['check']}** ({it['area']}, {it['impact']} impact / {it['effort']} effort) — {it['detail']}  \n   → {it['fix']}")
    out += ["", "### 2. Fix & optimize — all issues", ""]
    for area, items in ap["fix_and_optimize"].items():
        out.append(f"**{area}**")
        for it in items:
            out.append(f"- {ICON[it['status']]} {it['check']}: {it['detail']} → {it['fix']}")
            for ex in it["examples"][:3]:
                out.append(f"  - `{ex}`")
        out.append("")
    out += ["### 3. Test & monitor", "", "| Area | Metric | Baseline |", "|---|---|---|"]
    out += [f"| {m['area']} | {m['metric']} | {m['baseline']} |" for m in ap["test_and_monitor"]]
    out += ["", f"### 4. Re-audit regularly", "", ap["re_audit"]["note"], "", "## Quick wins", ""]
    for w in r["quick_wins"]:
        out.append(f"- {'✅' if w['status'] == 'done' else '⬜'} **{w['title']}**" + ("".join(f"\n  - {x}" for x in w["items"])))
    out += ["", "## Full checklist", ""]
    for a in r["areas"]:
        out.append(f"### {a['number']}. {a['name']} — {a['score']}/100")
        for c in a["checks"]:
            out.append(f"- {ICON.get(c['status'], '')} **{c['label']}** — {c['detail']}")
        out.append("")
    A = r.get("aeo")
    if A and not A.get("error"):
        out += [f"## AI search readiness (AEO): {A['score']}/100 — {A['band']['label']}", ""]
        if A.get("locked"):
            out += [f"_{A.get('issues_hidden', 0)} AI-search issues found — full detail and fixes are in the Pro report._", ""]
        out += ["| Crawler | Role | robots.txt | Live |", "|---|---|---|---|"]
        out += [f"| {b['bot']} | {b.get('role_label', b['role'])} | {b['robots']} | {b.get('live') or '—'} |" for b in A.get("bots", [])]
        out.append("")
        for a in A["areas"]:
            out.append(f"### {a['number']}. {a['name']} — {a['score']}/100")
            for c in a["checks"]:
                out.append(f"- {ICON.get(c['status'], '')} **{c['label']}**" + (f" — {c['detail']}" if c.get("detail") else "") + (f"  \n  → {c['fix']}" if c.get("fix") and c["status"] in ("warn", "fail") else ""))
            out.append("")
        if A.get("visibility") and A["visibility"].get("status") == "done":
            v = A["visibility"]
            out += [f"### AI answer visibility: {v['share_of_voice']}% share of voice ({v['cited']} citations, {v['mentioned']} mentions / {v['total']} answers)", ""]
        for k, f in (A.get("fixes") or {}).items():
            if f.get("code"):
                out += [f"### Fix: {f['title']} ({f['file']})", "", f["how"], "", "```", f["code"].rstrip(), "```", ""]
    if r.get("outreach_email"):
        out += ["## Outreach email draft", "", "```", r["outreach_email"], "```", ""]
    return "\n".join(out)
