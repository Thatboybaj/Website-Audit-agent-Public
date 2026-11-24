"""Client-facing HTML/PDF report — ledger-paper style (light version of the AuditPilot system), white-label ready."""
from __future__ import annotations

from jinja2 import BaseLoader, Environment

from .scoring import BANDS

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ host }} — Website audit</title>
<link href="https://fonts.googleapis.com/css2?family=Funnel+Display:wght@400;500;600&family=Inter+Tight:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{--ink:#0e1116;--paper:#f4f1ea;--card:#fbfaf6;--line:rgba(14,17,22,.1);--muted:#5d626b;--acc:{{ accent }};--pass:#1f9d5c;--warn:#c98a12;--fail:#d23f3f;--aeo:#2340d9}
*{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0;background:var(--paper);color:var(--ink);font:400 14.5px/1.55 "Inter Tight",system-ui,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:44px 36px 60px}
.m{font:500 10.5px "JetBrains Mono",monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
h1{font:500 64px/.95 "Funnel Display",sans-serif;letter-spacing:-.05em;margin:14px 0 8px}
h2{font:500 30px/1.05 "Funnel Display",sans-serif;letter-spacing:-.04em;margin:44px 0 14px;break-after:avoid}
h3{font:500 19px "Funnel Display",sans-serif;letter-spacing:-.02em;margin:0}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;border-bottom:1px solid var(--line);padding-bottom:16px}
.brand{display:flex;align-items:center;gap:10px;font:500 18px "Funnel Display",sans-serif}.brand img{height:30px}
.mk{width:20px;height:20px;border-radius:50%;border:2.2px solid var(--acc);position:relative}.mk:after{content:"";position:absolute;inset:4px;border-radius:50%;background:var(--ink)}
.host{font-size:15px;color:var(--muted)}
.scores{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:22px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px;break-inside:avoid}
.dark{background:var(--ink);color:var(--paper);border-color:var(--ink)}.dark .m{color:#a9aeb7}
.g{display:flex;gap:14px;align-items:center;margin-top:8px}
.band{display:inline-block;font:500 10px "JetBrains Mono",monospace;letter-spacing:.1em;text-transform:uppercase;padding:3px 8px;border-radius:999px;margin-bottom:6px}
.n3{display:flex;gap:18px;margin-top:10px}.n3 b{display:block;font:500 30px/1 "Funnel Display",sans-serif;letter-spacing:-.04em}.n3 span{font:400 10px "JetBrains Mono",monospace;text-transform:uppercase;color:var(--muted)}
.summary{white-space:pre-wrap;font-size:15px;margin:0}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
ol.prio{list-style:none;margin:0;padding:0;counter-reset:p}ol.prio li{display:grid;grid-template-columns:30px 1fr;gap:8px;padding:12px 0;border-top:1px solid var(--line);break-inside:avoid}
ol.prio li:before{counter-increment:p;content:counter(p,decimal-leading-zero);font:500 11px "JetBrains Mono",monospace;color:var(--muted);padding-top:3px}
.prio b{font-weight:600}.prio p{margin:3px 0 0;color:var(--muted)}.prio .fx{color:var(--ink)}
.tag{display:inline-block;font:500 9.5px "JetBrains Mono",monospace;letter-spacing:.08em;text-transform:uppercase;padding:2px 7px;border-radius:999px;border:1px solid var(--line);color:var(--muted);margin-right:4px}
.areas{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.ah{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px}.ah .s{font:500 34px/1 "Funnel Display",sans-serif;letter-spacing:-.04em}
.bar{height:4px;border-radius:4px;background:rgba(14,17,22,.08);margin-bottom:8px}.bar i{display:block;height:100%;border-radius:4px}
.ck{display:grid;grid-template-columns:14px 1fr;gap:8px;padding:7px 0;border-top:1px dashed var(--line);font-size:13px}
.ck i{width:9px;height:9px;border-radius:3px;margin-top:5px}.ck b{font-weight:600}.ck p{margin:1px 0 0;color:var(--muted)}.ck .fx{color:var(--ink)}
.p{background:var(--pass)}.w{background:var(--warn)}.f{background:var(--fail)}.s0{background:#c9c5bb}
table{width:100%;border-collapse:collapse;font-size:12.5px}th{font:500 9.5px "JetBrains Mono",monospace;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);text-align:left;padding:8px}
td{padding:8px;border-top:1px solid var(--line);vertical-align:top;word-break:break-word}
pre{margin:8px 0 0;background:#0e1116;color:#dfe4ff;border-radius:10px;padding:12px;font:11px/1.55 "JetBrains Mono",monospace;white-space:pre-wrap;word-break:break-all}
.chips span{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:4px 10px;margin:0 6px 6px 0;font-size:12.5px}
.lockbox{border:1px dashed var(--aeo);background:rgba(35,64,217,.05)}
.foot{margin-top:50px;padding-top:16px;border-top:1px solid var(--line);display:flex;justify-content:space-between;color:var(--muted);font-size:12.5px;gap:20px;flex-wrap:wrap}
.guide{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}.guide span{font:500 10px "JetBrains Mono",monospace;padding:3px 8px;border-radius:6px;color:#fff}
@page{size:A4;margin:12mm}
@media screen and (max-width:800px){.scores,.two,.areas{grid-template-columns:1fr}h1{font-size:44px}}
@media print{body{background:var(--paper)}.wrap{padding:0;max-width:none}h2{margin-top:26px}h1{font-size:52px}
.scores{grid-template-columns:repeat(4,1fr)}.two,.areas{grid-template-columns:1fr 1fr}.card{padding:14px;break-inside:auto}.ck,.prio li,tr{break-inside:avoid}.ck{font-size:12px;padding:5px 0}html{zoom:.86}}
</style></head><body><div class="wrap">
<div class="top">
  <div class="brand">{% if b.logo %}<img src="{{ b.logo }}" alt="{{ b.name }}">{% else %}<span class="mk"></span>{% endif %}{{ b.name }}</div>
  <div style="text-align:right"><div class="m">Website audit · {{ r.audited_at[:10] }}</div><div class="host">{{ pages_ok }} pages crawled</div></div>
</div>
<div class="m" style="margin-top:28px">SEO + AI search audit</div>
<h1>{{ host }}</h1>
<div class="host">{{ r.url }}</div>

<div class="scores">
  <div class="card"><div class="m">SEO health</div><div class="g">{{ ring(r.overall_score, col(r.overall_score)) }}<div><span class="band" style="background:{{ col(r.overall_score) }}22;color:{{ col(r.overall_score) }}">{{ r.band.label }}</span><div style="font-size:12.5px;color:var(--muted)">{{ r.band.description }}</div></div></div></div>
  <div class="card {{ 'lockbox' if A and A.locked }}"><div class="m">AI search readiness</div>{% if A and not A.error %}<div class="g">{{ ring(A.score, '#2340d9') }}<div><span class="band" style="background:rgba(35,64,217,.1);color:#2340d9">{{ A.band.label }}</span><div style="font-size:12.5px;color:var(--muted)">{{ 'Full AEO detail is in the Pro report.' if A.locked else 'Ready to be found and cited by AI assistants.' }}</div></div></div>{% else %}<p>Not run.</p>{% endif %}</div>
  <div class="card"><div class="m">Issues</div><div class="n3"><div><b style="color:var(--fail)">{{ r.action_plan.counts.critical }}</b><span>critical</span></div><div><b style="color:var(--warn)">{{ r.action_plan.counts.warnings }}</b><span>warnings</span></div><div><b style="color:var(--pass)">{{ r.action_plan.counts.passed }}</b><span>passed</span></div></div></div>
  <div class="card dark"><div class="m">AI crawlers</div>{% if A and A.bots %}{% set sb = A.bots|selectattr('role','equalto','search')|list %}<div class="n3"><div><b>{{ sb|rejectattr('robots','equalto','blocked')|list|length }}/{{ sb|length }}</b><span style="color:#a9aeb7">search bots allowed</span></div></div>
    <div style="font-size:12.5px;margin-top:8px;color:#a9aeb7">{{ (A.bots|selectattr('live','equalto','blocked')|list|length) ~ ' blocked by firewall' if A.bots|selectattr('live','equalto','blocked')|list else 'No firewall blocks detected' }}</div>{% else %}<p>—</p>{% endif %}</div>
</div>
<div class="guide">{% for floor, label, desc, color in bands %}<span style="background:{{ color }}">{{ floor }}+ {{ label }}</span>{% endfor %}</div>

<h2>Summary</h2>
<div class="two"><div class="card"><p class="summary">{{ r.summary }}</p></div>
<div class="card"><div class="m">Fix first</div><ol class="prio">{% for it in fixfirst %}<li><div><b>{{ it.check }}</b> <span class="tag">{{ it.area }}</span><span class="tag">{{ it.impact }} impact</span><p>{{ it.detail }}</p><p class="fx">→ {{ it.fix }}</p></div></li>{% endfor %}</ol></div></div>

<h2 class="pb">SEO audit · 10 areas</h2>
<div class="areas">{% for a in r.areas %}{{ area(a, false) }}{% endfor %}</div>

{% if A and not A.error %}
<h2 class="pb">AI search (AEO) audit</h2>
{% if A.locked %}
<div class="card lockbox"><h3>AI search readiness: {{ A.score }}/100 · {{ A.issues_hidden }} issues found</h3><p style="color:var(--muted)">The Pro report explains each AI-search issue, how to fix it, includes ready-to-paste llms.txt and schema markup, and tests whether AI answer engines cite this site today.</p>
<table><tr><th>Area</th><th>Score</th></tr>{% for a in A.areas %}<tr><td>{{ a.name }}</td><td>{{ a.score }}/100</td></tr>{% endfor %}</table></div>
{% else %}
{% if A.ai and A.ai.ai_description %}<div class="two"><div class="card"><div class="m">How an AI assistant would describe {{ A.brand }}</div><p class="summary">{{ A.ai.ai_description }}</p></div>
<div class="card"><div class="m">Facts AI can't find</div><ol class="prio">{% for m in A.ai.missing or [] %}<li><div>{{ m }}</div></li>{% else %}<li><div>Nothing important missing.</div></li>{% endfor %}</ol></div></div>{% endif %}
<div class="card" style="margin-top:12px"><div class="m">AI crawler access</div><table><tr><th>Crawler</th><th>Company</th><th>Role</th><th>Powers</th><th>robots.txt</th><th>Live</th></tr>
{% for b in A.bots %}<tr><td><b>{{ b.bot }}</b></td><td>{{ b.company }}</td><td>{{ b.role_label }}</td><td>{{ b.engine }}</td><td style="color:{{ 'var(--fail)' if b.robots=='blocked' else 'var(--pass)' }}">{{ b.robots }}</td><td>{{ b.live or '—' }}</td></tr>{% endfor %}</table></div>
{% if A.visibility and A.visibility.status == 'done' %}{% set v = A.visibility %}
<div class="card" style="margin-top:12px"><div class="m">AI answer visibility · {{ v.engines|join(' & ') }}</div><h3 style="margin:6px 0">Share of voice: {{ v.share_of_voice }}% ({{ v.cited }} citations, {{ v.mentioned }} mentions in {{ v.total }} answers)</h3>
<table><tr><th>Question</th><th>Engine</th><th>Result</th></tr>{% for x in v.results if not x.error %}<tr><td>{{ x.question }}</td><td>{{ x.engine }}</td><td>{{ 'cited' if x.cited else 'mentioned' if x.mentioned else 'absent' }}</td></tr>{% endfor %}</table>
{% if v.competitors %}<p style="margin:10px 0 0;color:var(--muted)">Cited instead: {{ v.competitors|map(attribute='domain')|join(', ') }}</p>{% endif %}</div>{% endif %}
<div class="areas" style="margin-top:12px">{% for a in A.areas %}{{ area(a, true) }}{% endfor %}</div>
<h2 class="pb">Ready-to-paste fixes</h2>
{% for k, f in (A.fixes or {}).items() %}<div class="card" style="margin-bottom:10px"><h3>{{ f.title }} <span class="tag">{{ f.file }}</span></h3><p style="color:var(--muted);margin:6px 0 0">{{ f.how }}</p><pre>{{ f.code }}</pre></div>{% endfor %}
{% endif %}{% endif %}

<h2 class="pb">Pages</h2>
<div class="card"><table><tr><th>Page</th><th>Status</th><th>Title len</th><th>Desc len</th><th>Words</th><th>H1</th><th>Load</th></tr>
{% for p in r.meta.pages[:30] %}<tr><td>{{ p.url }}</td><td>{{ p.status }}</td><td>{{ p.title_len if p.title_len is defined else '—' }}</td><td>{{ p.desc_len if p.desc_len is defined else '—' }}</td><td>{{ p.words }}</td><td>{{ p.h1 if p.h1 is defined else '—' }}</td><td>{{ p.ms }}ms</td></tr>{% endfor %}</table></div>
{% if r.tech %}<h2>Technology</h2><div class="card chips">{% for t in r.tech %}<span>{{ t.name }} <span class="m" style="font-size:9px">{{ t.category }}</span></span>{% endfor %}</div>{% endif %}
{% if show_email and r.outreach_email %}<h2>Outreach email</h2><div class="card"><p class="summary">{{ r.outreach_email }}</p></div>{% endif %}

<div class="foot"><div>{{ b.name }}{% if b.contact %} · {{ b.contact }}{% endif %}</div><div>{{ b.credit }}</div></div>
</div>
{% if print_mode %}<script>(function(){function go(){setTimeout(function(){window.print()},700)}if(document.readyState==='complete')go();else addEventListener('load',go)})();</script>{% endif %}
</body></html>"""

AREA = r"""<div class="card"><div class="ah"><h3>{{ a.number }} · {{ a.name }}</h3><span class="s" style="color:{{ '#2340d9' if aeo else col(a.score) }}">{{ a.score }}</span></div>
<div class="bar"><i style="width:{{ a.score }}%;background:{{ '#2340d9' if aeo else col(a.score) }}"></i></div><div class="m">{{ a.key_metric_label }}: {{ a.key_metric_value }}</div>
{% for c in a.checks %}<div class="ck"><i class="{{ {'pass':'p','warn':'w','fail':'f'}.get(c.status,'s0') }}"></i><div><b>{{ c.label }}</b>{% if c.detail %}<p>{{ c.detail }}</p>{% endif %}{% if c.fix and c.status in ('warn','fail') %}<p class="fx">→ {{ c.fix }}</p>{% endif %}</div></div>{% endfor %}</div>"""


def _col(s):
    return "#1f9d5c" if s >= 90 else "#6aa83a" if s >= 70 else "#c98a12" if s >= 50 else "#d9732b" if s >= 30 else "#d23f3f"


def _ring(s, color):
    from markupsafe import Markup
    C = 2 * 3.14159 * 38
    v = max(0, min(100, s or 0))
    return Markup(f'<svg width="92" height="92" viewBox="0 0 92 92"><circle cx="46" cy="46" r="38" fill="none" stroke="rgba(14,17,22,.08)" stroke-width="8"/>'
                  f'<circle cx="46" cy="46" r="38" fill="none" stroke="{color}" stroke-width="8" stroke-linecap="round" stroke-dasharray="{C * v / 100:.1f} {C:.1f}" transform="rotate(-90 46 46)"/>'
                  f'<text x="46" y="54" text-anchor="middle" font-family="Funnel Display,sans-serif" font-size="26" fill="#0e1116">{v}</text></svg>')


def to_html(report: dict, brand: str = "brightajiboye.com", show_email: bool = False, print_mode: bool = False, branding: dict | None = None) -> str:
    from urllib.parse import urlparse
    env = Environment(loader=BaseLoader(), autoescape=True)
    env.globals.update(col=_col, ring=_ring)
    area_t = env.from_string(AREA)
    from markupsafe import Markup
    env.globals["area"] = lambda a, aeo: Markup(area_t.render(a=a, aeo=aeo))
    b = branding or {}
    bb = {"name": b.get("name") or "AuditPilot", "logo": b.get("logo") or "", "contact": b.get("contact") or "",
          "credit": "" if b.get("name") else f"Audit by AuditPilot · {brand}"}
    accent = b.get("color") if b.get("color", "").startswith("#") and len(b.get("color", "")) in (4, 7) else "#2340d9"
    A = report.get("aeo")
    fix = list(report["action_plan"]["prioritize"])
    if A and not A.get("error") and not A.get("locked"):
        aeo_fix = [{"check": c["label"], "area": a["name"], "impact": c["impact"], "detail": c["detail"], "fix": c["fix"]}
                   for a in A["areas"] for c in a["checks"] if c["status"] == "fail" and c["impact"] == "high"][:3]
        fix = aeo_fix + fix
    host = (urlparse(report["url"]).hostname or report["url"]).removeprefix("www.")
    return env.from_string(TEMPLATE).render(r=report, A=A, b=bb, accent=accent, bands=BANDS, host=host, fixfirst=fix[:8],
                                            pages_ok=sum(1 for p in report["meta"]["pages"] if p["status"] == 200),
                                            show_email=show_email, print_mode=print_mode)


async def to_pdf(report: dict, brand: str = "brightajiboye.com", branding: dict | None = None) -> bytes:
    """Real PDF via headless Chromium (needs Playwright; not available on Vercel)."""
    from playwright.async_api import async_playwright
    html = to_html(report, brand=brand, branding=branding)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle", timeout=30000)
        await page.emulate_media(media="print")
        pdf = await page.pdf(format="A4", print_background=True, margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"})
        await browser.close()
    return pdf
