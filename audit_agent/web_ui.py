"""AuditPilot web app (served at "/"). Design system follows Bright's recent builds (Countersign):
ink #07080b / ledger #f4f1ea / blue #2340d9 + #8ea0ff, Funnel Display + Inter Tight + JetBrains Mono,
wireframe globe, inspector cards. One file, no build step."""
import json

from ._ui_css import CSS
from ._ui_js import JS

FAQ = [
    ("What is an AEO audit?", "An AEO (Answer Engine Optimization) audit checks whether AI assistants like ChatGPT, Perplexity, Claude and Google's AI Overviews can reach, read, trust and quote your website — and shows exactly what to fix so they recommend you."),
    ("What's the difference between SEO and AEO?", "SEO gets you ranked in search results. AEO gets you cited inside AI answers. They overlap, but AEO adds AI crawler access, answer-ready content, entity signals and machine-readable facts."),
    ("Is the SEO audit really free?", "Yes. The full SEO audit — 10 areas and 70+ checks, with a health score, action plan and PDF — is free. The detailed AEO audit, AI visibility test and ready-to-paste fixes are part of Pro."),
    ("How long does an audit take?", "Usually 20–60 seconds, depending on the site's speed and how many pages are crawled."),
    ("Do you store my website data?", "No. Reports are generated on demand and saved only in your own browser's history."),
]

APP_LLMS_TXT = """# __PRODUCT__

> __PRODUCT__ audits websites for search engines (SEO) and AI answer engines (AEO): technical SEO, speed, mobile, content, security, accessibility, AI crawler access, structured data and answer-readiness. Built by __BRAND__.

## Product
- [Run an audit](/): Free SEO audit with a health score and action plan; Pro adds the full AEO audit, AI visibility test and ready-to-paste fixes.
"""

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__PRODUCT__ — SEO & AI Search (AEO) Audit</title>
<meta name="description" content="Free SEO audit plus an AI search (AEO) readiness score. See if ChatGPT, Perplexity and Google AI Overviews can find, read and cite your website — and exactly what to fix.">
<meta property="og:title" content="__PRODUCT__ — Get found by Google. Get cited by AI.">
<meta property="og:description" content="Free SEO audit + AI search readiness score in about a minute.">
<meta property="og:type" content="website"><meta name="theme-color" content="#07080b">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='9' fill='%2307080b'/%3E%3Ccircle cx='16' cy='16' r='8.5' fill='none' stroke='%238ea0ff' stroke-width='2.4'/%3E%3Ccircle cx='16' cy='16' r='2.6' fill='%23f4f1ea'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Funnel+Display:wght@400;500;600;700&family=Inter+Tight:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script type="application/ld+json">__JSONLD__</script>
<style>__CSS__</style></head>
<body>
<svg class="globe" viewBox="0 0 900 900" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="1">
<circle cx="450" cy="450" r="430"/><ellipse cx="450" cy="450" rx="330" ry="430"/><ellipse cx="450" cy="450" rx="200" ry="430"/><ellipse cx="450" cy="450" rx="70" ry="430"/>
<ellipse cx="450" cy="450" rx="430" ry="330"/><ellipse cx="450" cy="450" rx="430" ry="200"/><ellipse cx="450" cy="450" rx="430" ry="70"/></g></svg>
<div class="glow" aria-hidden="true"></div>

<header class="nav">
  <a class="logo" href="/" aria-label="__PRODUCT__ home"><span class="mark"></span>__PRODUCT__</a>
  <nav class="links" aria-label="Main">
    <a href="#how" data-go="landing">How it works</a><a href="#aeo" data-go="landing">AEO</a><a href="#pricing" data-go="landing">Pricing</a>
    <a href="#" data-view="history">History</a>
  </nav>
  <div class="navr">
    <button class="plan" id="planPill" type="button"><span class="pdot"></span><span id="planLbl">Free</span></button>
    <button class="btn light sm" id="unlockBtn" type="button">Unlock Pro</button>
  </div>
</header>

<main id="app">
<!-- ===================== LANDING ===================== -->
<section id="landing" class="view on">
  <div class="hero wrap">
    <div class="hero-l">
      <div class="eyebrow"><span class="dot"></span>SEO + AI search audit</div>
      <h1>Get found by Google.<br><span class="grad">Get cited by AI.</span></h1>
      <p class="lede">One run checks the 70+ things search engines care about — and whether ChatGPT, Perplexity and Google's AI Overviews can reach, read, trust and quote your site.</p>
      <form id="auditForm" class="bar" autocomplete="off">
        <span class="bar-ico" aria-hidden="true">↗</span>
        <input id="url" type="text" inputmode="url" placeholder="yourwebsite.com" aria-label="Website address" required>
        <button class="btn light" id="go" type="submit">Run audit <span aria-hidden="true">→</span></button>
      </form>
      <div class="chips"><span class="chip"><i class="ok"></i>SEO audit · free</span><span class="chip"><i class="blue"></i>AEO audit · Pro</span><span class="chip muted" id="pagesChip">5 pages</span></div>
      <div class="err" id="err" role="alert"></div>
    </div>
    <div class="hero-r" id="inspector" aria-live="polite">
      <div class="card insp c1"><div class="ih"><span>01 · Crawl</span><span class="t">14:02</span></div><b>robots.txt, sitemap, 48 links</b><small>3 broken links · 1 redirect chain</small></div>
      <div class="card insp c2"><div class="ih"><span>02 · AI access</span><span class="t">14:02</span></div><b>PerplexityBot blocked by firewall</b><small class="warnc">robots.txt allows it · CDN returns 403</small></div>
      <div class="card insp c3"><div class="ih"><span>03 · Verdict</span><span class="t">14:03</span></div>
        <div class="vrow"><div><div class="mlabel">SEO health</div><div class="big">78</div></div><div><div class="mlabel">AI search readiness</div><div class="big blue">41</div></div></div>
        <small>Fix 6 things to get cited in AI answers.</small></div>
    </div>
  </div>

  <div class="wrap marquee"><span>Checks for</span><b>ChatGPT search</b><b>Perplexity</b><b>Google AI Overviews</b><b>Claude</b><b>Bing Copilot</b></div>

  <section class="wrap sec" id="aeo">
    <div class="sec-h"><div class="eyebrow"><span class="dot"></span>Two audits, one run</div><h2>Search engines rank pages.<br><span class="grad">Answer engines quote them.</span></h2></div>
    <div class="two">
      <div class="card pane"><div class="ph"><span class="mlabel">SEO audit</span><span class="tag ok">Free</span></div>
        <ol class="alist" id="seoList"></ol></div>
      <div class="card pane blue-edge"><div class="ph"><span class="mlabel">AEO audit</span><span class="tag blue">Pro</span></div>
        <ol class="alist" id="aeoList"></ol></div>
    </div>
  </section>

  <section class="wrap sec" id="how">
    <div class="sec-h"><div class="eyebrow"><span class="dot"></span>How it works</div><h2>From URL to fix list<br><span class="grad">in about a minute.</span></h2></div>
    <div class="three">
      <div class="card step"><span class="mlabel">01</span><h3>Crawl like a bot</h3><p>We read your pages, robots.txt, sitemap and every link — then knock on the door as GPTBot, PerplexityBot, Claude and Google to see who gets in.</p></div>
      <div class="card step"><span class="mlabel">02</span><h3>Score what matters</h3><p>70+ SEO checks and 40+ AEO checks, each pass / warn / fail, weighted by impact. Every finding shows its evidence.</p></div>
      <div class="card step"><span class="mlabel">03</span><h3>Get the fixes</h3><p>A prioritised action plan, plus ready-to-paste llms.txt, schema markup and robots.txt rules — and a test of whether AI already cites you.</p></div>
    </div>
  </section>

  <section class="wrap sec" id="pricing">
    <div class="sec-h"><div class="eyebrow"><span class="dot"></span>Pricing</div><h2>SEO is free.<br><span class="grad">AI visibility is Pro.</span></h2></div>
    <div class="two" id="priceCards"></div>
  </section>

  <section class="wrap sec" id="faq">
    <div class="sec-h"><div class="eyebrow"><span class="dot"></span>FAQ</div><h2>Questions, answered.</h2></div>
    <div class="faq">__FAQ__</div>
  </section>
</section>

<!-- ===================== RESULTS ===================== -->
<section id="results" class="view">
  <div class="wrap">
    <div class="rbar card">
      <div><div class="mlabel" id="rMeta"></div><h2 id="rUrl"></h2></div>
      <div class="acts">
        <button class="btn ghost sm" id="reAudit">Re-audit</button>
        <button class="btn ghost sm" id="cmpBtn">Compare</button>
        <button class="btn ghost sm" id="dlHtml">HTML</button>
        <button class="btn ghost sm" id="dlJson">JSON</button>
        <button class="btn light sm" id="dlPdf">Download PDF</button>
      </div>
    </div>
    <div class="scores" id="scores"></div>
    <div class="tabs" role="tablist" id="tabs"></div>
    <div id="panel"></div>
  </div>
</section>

<!-- ===================== COMPARE ===================== -->
<section id="compare" class="view"><div class="wrap">
  <div class="sec-h"><div class="eyebrow"><span class="dot"></span>Competitor comparison</div><h2>You vs. them.</h2></div>
  <form id="cmpForm" class="bar"><span class="bar-ico">⇄</span><input id="cmpUrl" placeholder="competitor.com" aria-label="Competitor website" required><button class="btn light" id="cmpGo">Compare →</button></form>
  <div class="err" id="cmpErr"></div>
  <div id="cmpOut"></div>
</div></section>

<!-- ===================== HISTORY ===================== -->
<section id="history" class="view"><div class="wrap">
  <div class="rbar card"><div><div class="mlabel">Saved in this browser</div><h2>History</h2></div>
    <div class="acts"><button class="btn ghost sm" id="csv">Export CSV</button><button class="btn ghost sm" id="clear">Clear</button></div></div>
  <div id="histBody" class="card tablewrap"></div>
</div></section>
</main>

<footer class="wrap foot">
  <div><span class="logo sm"><span class="mark"></span>__PRODUCT__</span><p>SEO + AI search audits. Built by <a href="https://__BRAND__">__BRAND__</a>.</p></div>
  <div class="mono">© <span id="yr"></span> · <a href="/llms.txt">llms.txt</a> · <a href="#" id="settingsLink">Settings</a></div>
</footer>

<!-- drawer + modals -->
<div class="drawer" id="drawer" aria-hidden="true"><aside class="dpanel card" id="dpanel" role="dialog" aria-modal="true"></aside></div>
<div class="modal" id="modal" aria-hidden="true"><div class="mbox card" id="mbox" role="dialog" aria-modal="true"></div></div>
<div class="toast" id="toast" role="status"></div>
<script>window.__CFG__=__CONFIG__;</script>
<script>__JS__</script>
</body></html>"""

EMBED = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__PRODUCT__</title>
<link href="https://fonts.googleapis.com/css2?family=Funnel+Display:wght@500;600&family=Inter+Tight:wght@400;600&family=JetBrains+Mono&display=swap" rel="stylesheet">
<style>*{box-sizing:border-box}body{margin:0;font-family:"Inter Tight",system-ui,sans-serif;background:#07080b;color:#f4f1ea}
.w{padding:22px;border:1px solid rgba(244,241,234,.08);border-radius:18px;background:radial-gradient(60% 80% at 100% 0,rgba(35,64,217,.35),transparent 70%),#0e1116}
.l{font:500 11px "JetBrains Mono",monospace;letter-spacing:.12em;text-transform:uppercase;color:#a9aeb7}
h2{font-family:"Funnel Display",sans-serif;font-weight:500;letter-spacing:-.03em;font-size:26px;margin:8px 0 14px}h2 span{color:#8ea0ff}
form{display:flex;gap:8px;background:#07080b;border:1px solid rgba(244,241,234,.12);border-radius:999px;padding:6px}
input{flex:1;min-width:0;background:none;border:0;color:#f4f1ea;font:500 15px "Inter Tight",sans-serif;padding:10px 14px;outline:none}
button{border:0;border-radius:999px;background:#f4f1ea;color:#0e1116;font:600 14px "Inter Tight",sans-serif;padding:0 18px;cursor:pointer}
small{display:block;margin-top:10px;color:#6b7079;font-size:12px}a{color:#8ea0ff}</style></head><body>
<div class="w"><div class="l">● Free SEO + AI search audit</div><h2>Is your site ready for <span>AI answers?</span></h2>
<form target="_blank" action="__ORIGIN__/" method="get"><input name="url" placeholder="yourwebsite.com" aria-label="Website address" required><button>Audit</button></form>
<small>Powered by <a href="__ORIGIN__/" target="_blank">__PRODUCT__</a></small></div></body></html>"""


def render_app(cfg: dict) -> str:
    faq_html = "".join(f'<details class="card qa"><summary>{q}</summary><p>{a}</p></details>' for q, a in FAQ)
    jsonld = json.dumps({"@context": "https://schema.org", "@graph": [
        {"@type": "SoftwareApplication", "name": cfg["product"], "applicationCategory": "BusinessApplication",
         "operatingSystem": "Web", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
         "description": "SEO audit and AI search (AEO) readiness audit for websites."},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]})
    return (HTML.replace("__CSS__", CSS).replace("__JS__", JS).replace("__FAQ__", faq_html)
            .replace("__JSONLD__", jsonld).replace("__CONFIG__", json.dumps(cfg))
            .replace("__PRODUCT__", cfg["product"]).replace("__BRAND__", cfg["brand"]))


def render_embed(cfg: dict, origin: str = "") -> str:
    return EMBED.replace("__PRODUCT__", cfg["product"]).replace("__ORIGIN__", origin)

