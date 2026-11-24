"""AuditPilot app (served at "/"). An app, not a marketing site: sidebar shell from the Pilot agents family
(LeadPilot, ProspectPilot) — light/dark dashboard, hairline cards, family blue — with AuditPilot's own identity:
violet AI-search accent, Instrument Sans + Geist Mono, scan-dial mark and dial gauges. One file, no build step."""
import json

from ._ui_css import CSS
from ._ui_js import JS

APP_LLMS_TXT = """# __PRODUCT__

> __PRODUCT__ audits websites for search engines (SEO) and AI answer engines (AEO): technical SEO, speed, mobile, content, security, accessibility, AI crawler access, structured data and answer-readiness. Built by __BRAND__.

## Product
- [Run an audit](/): Free SEO audit with a health score and action plan; Pro adds the full AEO audit, AI visibility test and ready-to-paste fixes.
"""

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__PRODUCT__ · SEO + AI search audits</title>
<meta name="description" content="__PRODUCT__ audits a website for search engines (SEO) and AI answer engines (AEO) and returns a scored fix list.">
<meta name="theme-color" content="#f4f5f7" media="(prefers-color-scheme: light)"><meta name="theme-color" content="#121318" media="(prefers-color-scheme: dark)">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%232b4ad8'/%3E%3Cstop offset='1' stop-color='%236f47e8'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='32' height='32' rx='9' fill='url(%23g)'/%3E%3Cpath d='M9 21.5a8 8 0 0 1 10.2-10.9' fill='none' stroke='%23fff' stroke-width='2.2' stroke-linecap='round'/%3E%3Cpath d='M16 17.5l4.2-4.6' stroke='%23fff' stroke-width='2.2' stroke-linecap='round'/%3E%3Ccircle cx='16' cy='17.5' r='1.9' fill='%23fff'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>__CSS__</style></head>
<body>
<div class="app">
<aside class="side" id="side" aria-label="Sidebar">
  <button class="logo" id="logo" type="button" aria-label="__PRODUCT__ — new audit"><svg class="mark" viewBox="0 0 32 32" aria-hidden="true"><defs><linearGradient id="apg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2b4ad8"/><stop offset="1" stop-color="#6f47e8"/></linearGradient></defs><rect width="32" height="32" rx="9" fill="url(#apg)"/><path d="M9 21.5a8 8 0 1 1 14 0" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" opacity=".55"/><path d="M9 21.5a8 8 0 0 1 10.2-10.9" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/><path d="M16 17.5l4.2-4.6" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/><circle cx="16" cy="17.5" r="1.9" fill="#fff"/></svg><span><span class="bname">__PRODUCT__</span><span class="bsub">SEO · AEO agent</span></span></button>
  <div class="navl">Workspace</div>
  <button class="nav on" data-view="new" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5M11 8v6M8 11h6"/></svg>New audit</button>
  <button class="nav" data-view="results" id="navResults" type="button" disabled><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19V5M4 19h16"/><path d="M8 15l3-4 3 2 4-6"/></svg>Report<span class="cnt" id="navHost"></span></button>
  <button class="nav" data-view="compare" id="navCompare" type="button" disabled><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 4v16M17 4v16M3 8h8M13 16h8"/></svg>Compare</button>
  <button class="nav" data-view="history" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/></svg>History<span class="cnt" id="histCnt"></span></button>
  <div class="navl">Account</div>
  <button class="nav" id="settingsLink" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>Settings</button>
  <button class="nav" id="planNav" type="button"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 17l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7z"/></svg>AEO access</button>
  <div class="sfoot">
    <div class="plancard"><button class="plan" id="planPill" type="button"><span class="pdot"></span><span id="planLbl">Free</span></button>
      <p id="planNote">SEO audit is free. AI search (AEO) detail is Pro.</p><button class="btn blue sm" id="unlockBtn" type="button">Unlock Pro</button></div>
    <div class="made">by <a href="https://__BRAND__" target="_blank" rel="noopener">__BRAND__</a> · <a href="/llms.txt">llms.txt</a></div>
  </div>
</aside>
<div class="scrim" id="scrim"></div>
<div class="main">
  <header class="topbar">
    <button class="btn ghost icon mtoggle" id="mtoggle" type="button" aria-label="Open menu"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
    <div><div class="crumb">__PRODUCT__ / <span id="crumb">Workspace</span></div><h1 id="pageTitle">New audit</h1></div>
    <div class="status" id="status"></div>
  </header>
  <main class="content" id="app">

  <!-- NEW AUDIT -->
  <section id="new" class="view on">
    <div class="card runner">
      <div class="mlabel">SEO + AI search audit</div>
      <h3>Audit a website</h3>
      <p>Crawls the site like Google and like ChatGPT, Perplexity and Claude, scores 10 SEO areas and 9 AI-search areas, and returns a ranked fix list.</p>
      <form id="auditForm" class="bar" autocomplete="off">
        <span class="bar-ico" aria-hidden="true">https://</span>
        <input id="url" type="text" inputmode="url" placeholder="yourwebsite.com" aria-label="Website address" required>
        <button class="btn light" id="go" type="submit">Run audit <span aria-hidden="true">→</span></button>
      </form>
      <div class="chips"><span class="chip"><i class="ok"></i>SEO · free</span><span class="chip"><i class="blue"></i>AEO · Pro</span><span class="chip" id="pagesChip">5 pages</span></div>
      <div class="err" id="err" role="alert"></div>
    </div>
    <div class="card log" id="inspector" aria-live="polite" hidden></div>
    <div class="card" id="recentCard" style="margin-bottom:14px" hidden><div class="ph" style="padding:14px 18px 0"><span class="mlabel">Recent audits</span><button class="btn ghost sm" type="button" data-view="history">View all</button></div><div class="tablewrap" id="recent"></div></div>
    <div class="two">
      <div class="card pane"><div class="ph"><span class="mlabel">SEO audit · 10 areas</span><span class="tag ok">Free</span></div><ol class="alist" id="seoList"></ol></div>
      <div class="card pane"><div class="ph"><span class="mlabel">AI search audit · 9 areas</span><span class="tag blue">Pro</span></div><ol class="alist" id="aeoList"></ol></div>
    </div>
  </section>

  <!-- REPORT -->
  <section id="results" class="view">
    <div class="rbar card">
      <div><div class="mlabel" id="rMeta"></div><h2 id="rUrl"></h2></div>
      <div class="acts">
        <button class="btn ghost sm" id="reAudit" type="button">Re-audit</button>
        <button class="btn ghost sm" id="cmpBtn" type="button">Compare</button>
        <button class="btn ghost sm" id="dlHtml" type="button">HTML</button>
        <button class="btn ghost sm" id="dlJson" type="button">JSON</button>
        <button class="btn light sm" id="dlPdf" type="button">Download PDF</button>
      </div>
    </div>
    <div class="scores" id="scores"></div>
    <div class="tabs" role="tablist" id="tabs"></div>
    <div id="panel"></div>
  </section>

  <!-- COMPARE -->
  <section id="compare" class="view">
    <div class="card runner"><div class="mlabel">Competitor comparison · Pro</div><h3>You vs. a competitor</h3>
      <p>Runs a second audit and lines both sites up area by area.</p>
      <form id="cmpForm" class="bar"><span class="bar-ico" aria-hidden="true">vs</span><input id="cmpUrl" placeholder="competitor.com" aria-label="Competitor website" required><button class="btn light" id="cmpGo">Compare →</button></form>
      <div class="err" id="cmpErr"></div></div>
    <div id="cmpOut"></div>
  </section>

  <!-- HISTORY -->
  <section id="history" class="view">
    <div class="phead"><div><h2>History</h2><p>Every audit is saved in this browser only. Click a row to reopen the full report.</p></div>
      <div class="acts"><button class="btn ghost sm" id="csv" type="button">Export CSV</button><button class="btn ghost sm" id="clear" type="button">Clear</button></div></div>
    <div id="histBody" class="card tablewrap"></div>
  </section>
  </main>
</div>
</div>

<div class="drawer" id="drawer" aria-hidden="true"><aside class="dpanel card" id="dpanel" role="dialog" aria-modal="true"></aside></div>
<div class="modal" id="modal" aria-hidden="true"><div class="mbox card" id="mbox" role="dialog" aria-modal="true"></div></div>
<div class="toast" id="toast" role="status"></div>
<script>window.__CFG__=__CONFIG__;</script>
<script>__JS__</script>
</body></html>"""

EMBED = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__PRODUCT__</title>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;600&family=Geist+Mono:wght@500&display=swap" rel="stylesheet">
<style>*{box-sizing:border-box}body{margin:0;font-family:"Instrument Sans",system-ui,sans-serif;background:transparent;color:#12141a}
.w{padding:22px;border:1px solid #e6e8ee;border-radius:14px;background:#fff;background-image:radial-gradient(#d9dde6 1px,transparent 1px);background-size:16px 16px}
.l{font:500 10.5px "Geist Mono",monospace;letter-spacing:.08em;text-transform:uppercase;color:#98a1b0}
h2{font-weight:600;letter-spacing:-.03em;font-size:22px;margin:6px 0 14px}h2 span{color:#6f47e8}
form{display:flex;gap:8px;background:#fff;border:1px solid #d7dbe3;border-radius:12px;padding:6px}
input{flex:1;min-width:0;background:none;border:0;color:#12141a;font:500 15px "Instrument Sans",sans-serif;padding:9px 10px;outline:none}
button{border:0;border-radius:9px;background:#2b4ad8;color:#fff;font:600 14px "Instrument Sans",sans-serif;padding:0 16px;cursor:pointer}
small{display:block;margin-top:10px;color:#98a1b0;font-size:12px}a{color:#2b4ad8}
@media(prefers-color-scheme:dark){body{color:#ecedf1}.w{background-color:#17181e;border-color:#272932;background-image:radial-gradient(#2a2d38 1px,transparent 1px)}form{background:#17181e;border-color:#323542}input{color:#ecedf1}h2 span{color:#a58bff}}</style></head><body>
<div class="w"><div class="l">Free SEO + AI search audit</div><h2>Is your site ready for <span>AI answers?</span></h2>
<form target="_blank" action="__ORIGIN__/" method="get"><input name="url" placeholder="yourwebsite.com" aria-label="Website address" required><button>Audit</button></form>
<small>Powered by <a href="__ORIGIN__/" target="_blank">__PRODUCT__</a></small></div></body></html>"""


def render_app(cfg: dict) -> str:
    return (HTML.replace("__CSS__", CSS).replace("__JS__", JS).replace("__CONFIG__", json.dumps(cfg))
            .replace("__PRODUCT__", cfg["product"]).replace("__BRAND__", cfg["brand"]))


def render_embed(cfg: dict, origin: str = "") -> str:
    return EMBED.replace("__PRODUCT__", cfg["product"]).replace("__ORIGIN__", origin)

