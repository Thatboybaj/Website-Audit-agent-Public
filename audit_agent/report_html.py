"""HTML report (HTML edition only) — styled after the Website Audit Cheat Sheet."""
from __future__ import annotations

from jinja2 import Environment, BaseLoader

from .scoring import BANDS

COLORS = ["#7c5cff", "#2e9e44", "#f5b82e", "#2f7fe0", "#f28c28", "#2f7fe0", "#e8508a", "#7c5cff", "#2e9e44", "#f5b82e"]
TINTS = ["#ece6ff", "#e3f3e6", "#fdf2d3", "#e2eefc", "#fde9d6", "#e2eefc", "#fce3ed", "#ece6ff", "#e3f3e6", "#fdf2d3"]
ICONS = [  # simple 24px line icons
    '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    '<path d="M4 16a8 8 0 1 1 16 0"/><path d="M12 16l4-5"/>',
    '<rect x="7" y="2.5" width="10" height="19" rx="2"/><path d="M11 18.5h2"/>',
    '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/>',
    '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
    '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    '<circle cx="12" cy="4.5" r="2"/><path d="M5 9h14M12 9v12M8 21l4-7 4 7"/>',
    '<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>',
]

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Website Audit — {{ r.url }}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{--ink:#141414;--muted:#6f6a62;--line:rgba(20,20,20,.08);--bg:#ebe8e2;--card:rgba(255,255,255,.66);--pass:#2e9e5b;--warn:#e3a23b;--fail:#d9443b;--mono:"JetBrains Mono",ui-monospace,monospace}
*{box-sizing:border-box}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);line-height:1.45;-webkit-font-smoothing:antialiased;background:radial-gradient(45% 30% at 10% 0%,#f3c39c 0,transparent 70%),radial-gradient(40% 30% at 90% 0%,#d6e19e 0,transparent 70%),radial-gradient(50% 40% at 80% 100%,#ecd0b4 0,transparent 70%),var(--bg);background-attachment:fixed}
.wrap{max-width:1180px;margin:0 auto;padding:40px 24px 60px}
h1{font-size:72px;line-height:.88;font-weight:900;letter-spacing:-.045em;margin:0}
.sub{font-size:22px;letter-spacing:8px;color:#555;font-weight:300;margin:8px 0 6px}
.eyebrow{font:500 11px var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.top{display:grid;grid-template-columns:1.2fr 1fr;gap:28px;align-items:start}
.panel{background:var(--card);border:1px solid rgba(255,255,255,.8);border-radius:24px;padding:24px;backdrop-filter:blur(20px);box-shadow:0 12px 40px rgba(40,30,15,.06)}
.meta{color:var(--muted);font-size:14px;margin-top:14px}.meta a{color:inherit}
.health{display:flex;gap:24px;align-items:center}
.band{display:inline-block;padding:4px 14px;border-radius:8px;font-weight:800;font-size:13px;letter-spacing:1px;text-transform:uppercase}
.guide div{display:flex;gap:12px;align-items:center;margin:7px 0;font-size:13px}
.guide b{display:inline-block;width:70px;text-align:center;color:#fff;border-radius:6px;padding:3px 0;font-size:12px}
.guide .on{outline:2px solid #111;outline-offset:2px;border-radius:6px}
h2{font-size:14px;letter-spacing:2px;text-transform:uppercase;margin:38px 0 14px}
.summary{font-size:15px;white-space:pre-wrap}
.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px}
.card{background:var(--card);border:1px solid rgba(255,255,255,.8);border-radius:22px;padding:18px;display:flex;flex-direction:column;backdrop-filter:blur(20px);box-shadow:0 10px 30px rgba(40,30,15,.05)}
.num{width:26px;height:26px;border-radius:50%;color:#fff;font-weight:800;font-size:13px;display:grid;place-items:center}
.ic{width:60px;height:60px;border-radius:50%;display:grid;place-items:center;margin:-4px auto 8px}
.ic svg{width:28px;height:28px;fill:none;stroke:#111;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
.card h3{font-size:14px;text-transform:uppercase;text-align:center;margin:0 0 10px;letter-spacing:.3px}
.score{font-size:30px;font-weight:900;text-align:center;margin-bottom:8px}.score small{font-size:13px;color:var(--muted);font-weight:500}
.checks{list-style:none;padding:0;margin:0 0 12px;flex:1}
.checks li{font-size:12.5px;margin:5px 0}
.checks details summary{cursor:pointer;list-style:none;display:flex;gap:7px;align-items:flex-start}
.checks details summary::-webkit-details-marker{display:none}
.dot{flex:none;width:15px;height:15px;border-radius:50%;margin-top:1px;color:#fff;font-size:10px;display:grid;place-items:center;font-weight:900}
.pass{background:var(--pass)}.warn{background:var(--warn)}.fail{background:var(--fail)}.info,.skip{background:#b8b3a8}
.det{font-size:12px;color:#444;background:#faf8f3;border-radius:8px;padding:8px 10px;margin:6px 0 4px 22px}
.det .fix{color:#111;margin-top:4px}.det code{font-size:11px;display:block;color:#666;word-break:break-all}
.km{background:rgba(255,255,255,.6);border:0;border-radius:14px;padding:9px 11px;display:flex;justify-content:space-between;align-items:center}
.km span{font-size:10px;letter-spacing:1px;font-weight:800;text-transform:uppercase}.km b{font-size:12px}.km strong{font-size:16px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.step{display:flex;gap:14px;padding:12px 0;border-bottom:1px solid var(--line)}.step:last-child{border:0}
.step .n{flex:none;width:26px;height:26px;border-radius:50%;background:#d8f36a;color:#141414!important;color:#fff;display:grid;place-items:center;font-weight:800;font-size:13px}
.step h4{margin:0 0 4px;font-size:13px;letter-spacing:1px;text-transform:uppercase}
.step ol,.step ul{margin:6px 0 0;padding-left:18px;font-size:13px}.step li{margin:4px 0}
.tag{font-size:10px;padding:1px 6px;border-radius:5px;background:#f0ede6;color:#555;margin-left:4px;white-space:nowrap}
.wins{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}
.win{background:#151515;color:#fff;border-radius:18px;padding:16px;font-size:13px}.win ul{color:#c9c4ba!important}
.win b{display:block;margin-bottom:6px}.win ul{padding-left:16px;margin:0;color:#444;font-size:12px}
.done{color:var(--pass);font-weight:700}
table{width:100%;border-collapse:collapse;font-size:13px}td,th{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left}
.shots{display:flex;gap:18px;align-items:flex-start}.shots img{border-radius:10px;border:1px solid var(--line);height:400px;object-fit:cover;object-position:top}
pre{white-space:pre-wrap;font-family:inherit;font-size:14px;margin:0}
.foot{margin-top:40px;background:#151515;color:#fff;border-radius:14px;padding:18px 24px;display:flex;justify-content:space-between;gap:20px;font-size:14px}
.up{color:var(--pass)}.down{color:var(--fail)}
@media(max-width:1000px){.grid,.wins{grid-template-columns:repeat(2,1fr)}.top,.cols{grid-template-columns:1fr}h1{font-size:44px}}
@page{size:A4;margin:10mm}
@media print{*{-webkit-print-color-adjust:exact;print-color-adjust:exact}body{background:#f4f2ee!important}.wrap{max-width:none;padding:0}
html{zoom:.68}.top{grid-template-columns:1.2fr 1fr!important}.cols{grid-template-columns:1fr 1fr!important}h1{font-size:60px}.grid{grid-template-columns:repeat(3,1fr)}.wins{grid-template-columns:repeat(3,1fr)}
.panel.health,.guide,.win,tr,.checks li,.step .n{break-inside:avoid}.card,.step{break-inside:auto}.panel,.card{backdrop-filter:none;box-shadow:none}h2{break-after:avoid}.shots img{height:300px}}
</style></head><body><div class="wrap">

<div class="top">
  <div>
    <h1>WEBSITE<br>AUDIT</h1>
    <div class="sub">REPORT</div>
    <div class="eyebrow">Analyze · Improve · Grow</div>
    <div class="meta"><a href="{{ r.url }}">{{ r.url }}</a> · {{ r.audited_at[:10] }} · {{ r.pages_crawled }} pages crawled<br>
    PageSpeed {{ 'on' if r.meta.psi else 'off' }} · Browser rendering {{ 'on' if r.meta.browser else 'off' }} · AI {{ 'on' if r.meta.ai else 'off' }}</div>
  </div>
  <div class="panel health" style="background:#151515;color:#fff;border:0">
    <svg width="170" height="170" viewBox="0 0 170 170">
      <circle cx="85" cy="85" r="70" fill="none" stroke="#2a2925" stroke-width="16"/>
      <circle cx="85" cy="85" r="70" fill="none" stroke="{{ r.band.color }}" stroke-width="16" stroke-linecap="round"
        stroke-dasharray="{{ (r.overall_score/100*439.8)|round(1) }} 439.8" transform="rotate(-90 85 85)"/>
      <text x="85" y="92" text-anchor="middle" font-size="50" font-weight="900" font-family="Inter,system-ui" fill="#fff">{{ r.overall_score }}</text>
      <text x="85" y="116" text-anchor="middle" font-size="14" fill="#777" font-family="Inter,system-ui">/100</text>
    </svg>
    <div>
      <div class="eyebrow">Overall health score</div>
      <div style="margin:8px 0"><span class="band" style="background:{{ r.band.color }}22;color:{{ r.band.color }}">{{ r.band.label }}</span></div>
      <div style="font-size:14px;color:#bdb8ae">{{ r.band.description }}</div>
      {% if r.comparison %}<div style="margin-top:8px;font-size:14px" class="{{ 'up' if r.comparison.overall_delta >= 0 else 'down' }}">
        {{ '%+d'|format(r.comparison.overall_delta) }} since {{ (r.comparison.previous_date or '')[:10] }}</div>{% endif %}
      <div style="margin-top:10px;font-size:13px">❌ {{ r.action_plan.counts.critical }} critical · ⚠️ {{ r.action_plan.counts.warnings }} warnings · ✅ {{ r.action_plan.counts.passed }} passed</div>
    </div>
  </div>
</div>

<div class="cols" style="margin-top:22px">
  <div class="panel"><div class="eyebrow" style="margin-bottom:10px">Executive summary</div><div class="summary">{{ r.summary }}</div></div>
  <div class="panel guide"><div class="eyebrow" style="margin-bottom:6px">Audit scoring guide</div>
    {% for floor, label, desc, color in bands %}
    <div><b style="background:{{ color }}" class="{{ 'on' if r.band.label == label }}">{{ floor }}–{{ 100 if floor == 90 else (29 if floor == 0 else floor + 19) }}</b><span><strong>{{ label }}</strong> — {{ desc }}</span></div>
    {% endfor %}
  </div>
</div>

{% if r.meta.screenshots %}
<h2>How visitors see it</h2>
<div class="panel shots">
  {% if r.meta.screenshots.desktop %}<img src="{{ r.meta.screenshots.desktop }}" alt="Desktop first screen" style="width:68%">{% endif %}
  {% if r.meta.screenshots.mobile %}<img src="{{ r.meta.screenshots.mobile }}" alt="Mobile first screen" style="width:24%">{% endif %}
</div>{% endif %}

<h2>The 10 core areas</h2>
<div class="grid">
{% for a in r.areas %}{% set i = loop.index0 %}
  <div class="card">
    <div class="num" style="background:{{ colors[i] }}">{{ a.number }}</div>
    <div class="ic" style="background:{{ tints[i] }}"><svg viewBox="0 0 24 24">{{ icons[i]|safe }}</svg></div>
    <h3>{{ a.name }}</h3>
    <div class="score" style="color:{{ band(a.score).color }}">{{ a.score }}<small>/100</small>
      {% if r.comparison and r.comparison.areas[a.key] and r.comparison.areas[a.key].delta %}<small class="{{ 'up' if r.comparison.areas[a.key].delta > 0 else 'down' }}">{{ '%+d'|format(r.comparison.areas[a.key].delta) }}</small>{% endif %}</div>
    <ul class="checks">
    {% for c in a.checks %}<li><details><summary><span class="dot {{ c.status }}">{{ {'pass':'✓','warn':'!','fail':'✕','info':'i','skip':'–'}[c.status] }}</span><span>{{ c.label }}</span></summary>
      <div class="det">{{ c.detail }}{% if c.fix and c.status in ('warn','fail') %}<div class="fix"><b>Fix:</b> {{ c.fix }}</div>{% endif %}
      {% for p in c.pages[:6] %}<code>{{ p }}</code>{% endfor %}</div></details></li>{% endfor %}
    </ul>
    <div class="km"><div><span style="color:{{ colors[i] }}">Key metric</span><br><b>{{ a.key_metric_label }}</b></div><strong>{{ a.key_metric_value }}</strong></div>
  </div>
{% endfor %}
</div>

<h2>Audit action plan</h2>
<div class="panel">
  <div class="step"><div class="n">1</div><div><h4>Prioritize</h4><div style="font-size:13px;color:#555">Critical issues first — high impact, easy to fix.</div>
    <ol>{% for it in r.action_plan.prioritize %}<li><b>{{ it.check }}</b> <span class="tag">{{ it.area }}</span><span class="tag">{{ it.impact }} impact</span><span class="tag">{{ it.effort }}</span><br>{{ it.detail }}<br><i>→ {{ it.fix }}</i></li>{% endfor %}</ol></div></div>
  <div class="step"><div class="n">2</div><div style="flex:1"><h4>Fix & optimize</h4><div style="font-size:13px;color:#555">Every open issue, grouped by area.</div>
    {% for area, items in r.action_plan.fix_and_optimize.items() %}<div style="margin-top:10px;font-size:13px"><b>{{ area }}</b><ul>
    {% for it in items %}<li><span class="dot {{ it.status }}" style="display:inline-grid;vertical-align:-3px">{{ '✕' if it.status == 'fail' else '!' }}</span> {{ it.check }} — {{ it.fix }}</li>{% endfor %}</ul></div>{% endfor %}</div></div>
  <div class="step"><div class="n">3</div><div style="flex:1"><h4>Test & monitor</h4><div style="font-size:13px;color:#555">Track these key metrics after each change.</div>
    <table><tr><th>Area</th><th>Metric</th><th>Baseline</th></tr>{% for m in r.action_plan.test_and_monitor %}<tr><td>{{ m.area }}</td><td>{{ m.metric }}</td><td><b>{{ m.baseline }}</b></td></tr>{% endfor %}</table></div></div>
  <div class="step"><div class="n">4</div><div><h4>Re-audit regularly</h4><div style="font-size:13px">Recommended cadence: <b>{{ r.action_plan.re_audit.cadence }}</b>. {{ r.action_plan.re_audit.note }}</div></div></div>
</div>

<h2>Quick wins to check first</h2>
<div class="wins">{% for w in r.quick_wins %}<div class="win"><b>{{ w.title }}</b>
  {% if w.status == 'done' %}<span class="done">✓ Looks good</span>{% else %}<ul>{% for x in w['items'] %}<li>{{ x }}</li>{% endfor %}</ul>{% endif %}</div>{% endfor %}</div>

{% if show_email %}<h2>Outreach email draft</h2><div class="panel"><pre>{{ r.outreach_email }}</pre></div>{% endif %}

<div class="foot"><div><b>KEY TAKEAWAY</b></div><div>A regular website audit helps you find issues, improve user experience, boost SEO and drive better results. <b>Audit. Optimize. Grow.</b></div><div>{{ brand }}</div></div>
</div>
<script>
function openAll(){document.querySelectorAll('details').forEach(function(d){d.open=true})}
addEventListener('beforeprint',openAll);
{% if print_mode %}(function(){function go(){openAll();setTimeout(function(){window.print()},600)}
if(document.readyState==='complete')go();else addEventListener('load',go)})();{% endif %}
</script></body></html>"""


def to_html(report: dict, brand: str = "brightajiboye.com", show_email: bool = False, print_mode: bool = False) -> str:
    from .scoring import band
    env = Environment(loader=BaseLoader(), autoescape=True)
    tpl = env.from_string(TEMPLATE)
    return tpl.render(r=report, colors=COLORS, tints=TINTS, icons=ICONS, bands=BANDS, band=band,
                      brand=brand, show_email=show_email, print_mode=print_mode)


async def to_pdf(report: dict, brand: str = "brightajiboye.com") -> bytes:
    """Real PDF via headless Chromium (needs Playwright; not available on Vercel)."""
    from playwright.async_api import async_playwright
    html = to_html(report, brand=brand).replace("addEventListener('beforeprint',openAll);", "openAll();")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle", timeout=30000)
        await page.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
        await page.emulate_media(media="print")
        pdf = await page.pdf(format="A4", print_background=True, margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"})
        await browser.close()
    return pdf
