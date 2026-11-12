"""Single-page web app served at "/": one URL per audit, results rendered as a dashboard.
Owner mode (access key = AUDIT_API_TOKEN) lifts the public demo limits."""

APP_HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Website Audit — __BRAND__</title>
<meta name="description" content="Audit any website across 10 core areas — SEO, performance, mobile, UX, conversion, content, security, accessibility and analytics — and get a prioritized action plan.">
<meta property="og:title" content="Website Audit"><meta property="og:description" content="Score any website across 10 core areas in about a minute.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{--ink:#141414;--muted:#6f6a62;--line:rgba(20,20,20,.08);--glass:rgba(255,255,255,.62);--glass-b:rgba(255,255,255,.75);
--lime:#d8f36a;--dark:#151515;--r:24px;--ex:#2e9e5b;--gd:#8bbf3f;--ni:#e3a23b;--po:#e0712f;--cr:#d9443b;
--mono:"JetBrains Mono",ui-monospace,monospace}
*{box-sizing:border-box}[hidden]{display:none!important}html{scroll-behavior:smooth}
body{margin:0;font-family:Inter,ui-sans-serif,system-ui,sans-serif;color:var(--ink);background:#ebe8e2;min-height:100vh;-webkit-font-smoothing:antialiased}
body:before{content:"";position:fixed;inset:-20%;z-index:-1;filter:blur(70px);opacity:.85;
background:radial-gradient(40% 35% at 12% 8%,#f3b483 0,transparent 70%),radial-gradient(35% 35% at 88% 4%,#cfdc8f 0,transparent 70%),
radial-gradient(40% 40% at 78% 92%,#e9c4a2 0,transparent 70%),radial-gradient(30% 30% at 20% 85%,#d9d3c6 0,transparent 70%)}
.wrap{max-width:1240px;margin:0 auto;padding:22px 24px 60px}
.glass{background:var(--glass);border:1px solid var(--glass-b);border-radius:var(--r);backdrop-filter:blur(22px) saturate(140%);-webkit-backdrop-filter:blur(22px) saturate(140%);box-shadow:0 12px 40px rgba(40,30,15,.06)}
.dark{background:var(--dark);color:#fff;border-radius:var(--r)}
.label{font:500 11px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.dark .label{color:#9a968e}
/* nav */
nav{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 12px 10px 18px}
.logo{display:flex;align-items:center;gap:10px;font-weight:800;letter-spacing:-.02em}
.logo i{width:30px;height:30px;border-radius:10px;background:var(--dark);display:grid;place-items:center}
.logo i:after{content:"";width:12px;height:12px;border-radius:50%;background:var(--lime)}
.tabs{display:flex;gap:4px;background:rgba(255,255,255,.55);border:1px solid var(--line);border-radius:999px;padding:4px}
.tabs button{border:0;background:none;font:600 13px Inter,sans-serif;padding:8px 16px;border-radius:999px;cursor:pointer;color:var(--muted)}
.tabs button.on{background:var(--dark);color:#fff}
.navr{display:flex;gap:10px;align-items:center}
.pill{border:1px solid var(--line);background:rgba(255,255,255,.6);border-radius:999px;padding:8px 14px;font:500 12px var(--mono);display:flex;gap:8px;align-items:center;cursor:pointer;color:var(--ink)}
.pill b{font-weight:500}.dot{width:8px;height:8px;border-radius:50%;background:#b9b4aa}.dot.on{background:var(--ex);box-shadow:0 0 0 3px rgba(46,158,91,.18)}
/* hero */
.hero{display:grid;grid-template-columns:1.25fr 1fr;gap:16px;margin-top:16px}
.intro{padding:34px}
h1{font-size:clamp(46px,7vw,86px);line-height:.9;letter-spacing:-.045em;margin:14px 0 16px;font-weight:900}
.intro p{color:#4b4740;font-size:16px;max-width:460px;margin:0 0 24px}
form{display:flex;gap:8px;background:#fff;border-radius:18px;padding:7px;border:1px solid var(--line);box-shadow:0 6px 20px rgba(0,0,0,.04)}
form input{flex:1;min-width:0;border:0;outline:none;font:500 16px Inter,sans-serif;padding:12px 14px;background:transparent}
.btn{border:0;background:var(--dark);color:#fff;font:700 14px Inter,sans-serif;padding:0 22px;border-radius:12px;cursor:pointer;display:inline-flex;align-items:center;gap:8px;justify-content:center;min-height:44px;text-decoration:none}
.btn.lime{background:var(--lime);color:var(--ink)}.btn.ghost{background:rgba(255,255,255,.7);color:var(--ink);border:1px solid var(--line)}
.btn:disabled{opacity:.55;cursor:wait}
.opts{display:flex;gap:16px;align-items:center;margin-top:14px;flex-wrap:wrap;font-size:13px;color:var(--muted)}
.opts label{display:flex;gap:6px;align-items:center;cursor:pointer}
.opts select{font:inherit;border:1px solid var(--line);border-radius:8px;padding:4px 6px;background:#fff}
.err{color:var(--cr);font-size:14px;margin-top:10px;min-height:18px}
.side{display:grid;grid-template-rows:auto 1fr;gap:16px}
.quota{padding:24px;display:flex;justify-content:space-between;align-items:flex-end}
.quota .big{font-size:56px;font-weight:800;letter-spacing:-.04em;line-height:1}
.quota .big small{font-size:20px;color:#8f8a80;font-weight:600}
.bar{height:8px;border-radius:9px;background:rgba(255,255,255,.12);overflow:hidden;margin-top:12px;width:180px}.bar i{display:block;height:100%;background:var(--lime);border-radius:9px}
.areas10{padding:20px;display:grid;grid-template-columns:repeat(2,1fr);gap:8px;align-content:start}
.ar{display:flex;align-items:center;gap:10px;font-size:13px;font-weight:600;padding:8px 10px;border-radius:12px;background:rgba(255,255,255,.55);transition:.25s}
.ar em{font:500 11px var(--mono);font-style:normal;color:var(--muted);width:20px}
.loading .ar{opacity:.4}.loading .ar.on{opacity:1;background:var(--dark);color:#fff}.loading .ar.on em{color:var(--lime)}
/* results */
#results{margin-top:16px;display:none}
.rhead{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:18px 22px;flex-wrap:wrap}
.rhead h2{margin:0;font-size:22px;letter-spacing:-.02em;word-break:break-all}.rhead .acts{display:flex;gap:8px;flex-wrap:wrap}
.bento{display:grid;grid-template-columns:repeat(12,1fr);gap:16px;margin-top:16px}
.c4{grid-column:span 4}.c5{grid-column:span 5}.c7{grid-column:span 7}.c8{grid-column:span 8}.c12{grid-column:span 12}.c3{grid-column:span 3}.c6{grid-column:span 6}
.card{padding:22px}
.gauge{display:flex;flex-direction:column;align-items:center;text-align:center;padding:24px}
.gauge svg{width:100%;max-width:300px}
.band{display:inline-block;padding:6px 14px;border-radius:999px;font:600 12px var(--mono);letter-spacing:.06em;text-transform:uppercase;margin-top:6px}
.counts{display:flex;gap:18px;margin-top:16px;font:500 12px var(--mono);color:#bdb8ae}.counts b{display:block;font:800 26px Inter,sans-serif;color:#fff;letter-spacing:-.02em}
.summary{font-size:15px;line-height:1.6;color:#2c2924;white-space:pre-wrap;margin-top:12px}
.metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-top:16px}
.metric{background:rgba(255,255,255,.6);border-radius:16px;padding:12px}.metric b{display:block;font-size:20px;letter-spacing:-.02em;margin-top:8px}
.grid10{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-top:16px}
.area{padding:18px;display:flex;flex-direction:column;cursor:pointer;transition:transform .2s}
.area:hover{transform:translateY(-2px)}
.area .top{display:flex;justify-content:space-between;align-items:flex-start}
.ic{width:42px;height:42px;border-radius:14px;display:grid;place-items:center}
.ic svg{width:22px;height:22px;fill:none;stroke:#141414;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
.area h3{font-size:15px;margin:14px 0 2px;letter-spacing:-.01em}
.area .sc{font-size:40px;font-weight:800;letter-spacing:-.04em;margin:6px 0 2px}.area .sc small{font-size:14px;color:var(--muted);font-weight:600}
.mini{height:6px;border-radius:6px;background:rgba(20,20,20,.07);overflow:hidden}.mini i{display:block;height:100%;border-radius:6px}
.km{display:flex;justify-content:space-between;margin-top:12px;font-size:12px}.km span{color:var(--muted)}
.dots{display:flex;gap:4px;margin-top:12px;flex-wrap:wrap}.dots i{width:9px;height:9px;border-radius:3px}
.p{background:var(--ex)}.w{background:var(--ni)}.f{background:var(--cr)}.s{background:#c9c4ba}
.plan li{margin:0 0 14px;padding-left:4px}.plan ol{padding-left:22px;margin:14px 0 0}
.plan b{font-size:14px}.plan .meta{display:flex;gap:6px;margin:5px 0;flex-wrap:wrap}
.tag{font:500 10px var(--mono);text-transform:uppercase;letter-spacing:.06em;padding:3px 7px;border-radius:6px;background:rgba(20,20,20,.06);color:#57524a}
.plan p{margin:2px 0;font-size:13px;color:#4b4740}.plan .fix{color:var(--ink)}
.wins{display:grid;gap:8px;margin-top:14px}.win{display:flex;gap:10px;align-items:flex-start;font-size:13px;padding:10px 12px;border-radius:14px;background:rgba(255,255,255,.08)}
.win i{flex:none;width:18px;height:18px;border-radius:6px;border:1.5px solid #6f6b63;margin-top:1px}.win.done i{background:var(--lime);border-color:var(--lime)}
.win small{display:block;color:#a8a399;margin-top:3px}
pre.email{white-space:pre-wrap;font:14px/1.6 Inter,sans-serif;margin:14px 0 0;background:rgba(255,255,255,.6);padding:16px;border-radius:16px}
/* drawer */
.drawer{position:fixed;inset:0;background:rgba(20,18,14,.35);display:none;z-index:20}
.drawer.on{display:block}
.panel{position:absolute;right:12px;top:12px;bottom:12px;width:min(520px,calc(100% - 24px));overflow:auto;padding:26px;background:rgba(250,248,244,.92);backdrop-filter:blur(24px)}
.chk{border-top:1px solid var(--line);padding:14px 0}.chk h4{margin:0;font-size:14px;display:flex;gap:8px;align-items:center}
.chk p{margin:6px 0 0;font-size:13px;color:#4b4740}.chk code{display:block;font:11px var(--mono);color:#7a756c;margin-top:4px;word-break:break-all}
.st{width:10px;height:10px;border-radius:3px;flex:none}
/* history */
#history{display:none;margin-top:16px}
table{width:100%;border-collapse:collapse;font-size:14px}th{text-align:left;font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.06em;color:var(--muted);padding:12px}
td{padding:12px;border-top:1px solid var(--line)}tr.row{cursor:pointer}tr.row:hover td{background:rgba(255,255,255,.5)}
.sp{display:inline-block;min-width:44px;text-align:center;padding:4px 8px;border-radius:8px;color:#fff;font-weight:700}
.empty{padding:40px;text-align:center;color:var(--muted)}
/* modal */
.modal{position:fixed;inset:0;background:rgba(20,18,14,.35);display:none;place-items:center;z-index:30}.modal.on{display:grid}
.modal .box{width:min(440px,calc(100% - 32px));padding:26px;background:rgba(250,248,244,.95)}
.modal input{width:100%;font:500 15px var(--mono);padding:12px 14px;border-radius:12px;border:1px solid var(--line);margin:14px 0}
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--dark);color:#fff;padding:10px 16px;border-radius:12px;font-size:14px;opacity:0;transition:.3s;pointer-events:none;z-index:40}.toast.on{opacity:1}
footer{margin-top:28px;display:flex;justify-content:space-between;font-size:13px;color:var(--muted);flex-wrap:wrap;gap:8px}footer a{color:var(--ink)}
@media(max-width:1000px){.hero{grid-template-columns:1fr}.grid10{grid-template-columns:repeat(2,1fr)}.c4,.c5,.c7,.c8,.c3,.c6{grid-column:span 12}.metrics{grid-template-columns:repeat(2,1fr)}.tabs button{padding:7px 11px}.logo span{display:none}}
@media(max-width:560px){form{flex-direction:column}.btn{min-height:48px}.intro{padding:24px}.grid10{grid-template-columns:1fr}}
@media print{body:before,nav,.hero,.rhead .acts,footer{display:none}#results{display:block!important}}
</style></head><body>
<div class="wrap">
<nav class="glass">
  <div class="logo"><i></i>Audit<span style="color:var(--muted);font-weight:600">/__BRANDSHORT__</span></div>
  <div class="tabs"><button class="on" data-tab="audit">Audit</button><button data-tab="history">History</button></div>
  <div class="navr"><button class="pill" id="keyBtn"><span class="dot" id="keyDot"></span><b id="keyLbl">Demo mode</b></button></div>
</nav>

<section class="hero" id="hero">
  <div class="glass intro">
    <div class="label">Website audit · 10 core areas</div>
    <h1>Audit any<br>website.</h1>
    <p>Get a health score out of 100, a breakdown across technical SEO, performance, mobile, UX, conversion, content, security, accessibility and analytics — plus a prioritized action plan.</p>
    <form id="f" autocomplete="off">
      <input id="url" type="text" inputmode="url" placeholder="yourwebsite.com" aria-label="Website address" required>
      <button class="btn" id="go" type="submit">Run audit</button>
    </form>
    <div class="opts" id="opts">
      <label>Pages <select id="pages"></select></label>
      <label id="aiOpt" hidden><input type="checkbox" id="ai"> AI summary &amp; email</label>
      <span id="modeNote"></span>
    </div>
    <div class="err" id="err" role="alert"></div>
  </div>
  <div class="side">
    <div class="dark quota">
      <div><div class="label">Audits today</div><div class="big" id="qNum">0<small> / 200</small></div><div class="bar"><i id="qBar" style="width:0"></i></div></div>
      <div style="text-align:right"><div class="label">Avg score</div><div style="font-size:30px;font-weight:800;margin-top:8px" id="qAvg">—</div></div>
    </div>
    <div class="glass areas10"><div class="label" style="grid-column:1/-1;margin:4px 2px 6px">What gets checked · 63 checks</div><div id="areas10" style="display:contents"></div><div style="grid-column:1/-1;margin-top:10px;font-size:13px;color:var(--muted);line-height:1.5">Each check is scored pass / warning / fail and weighted by impact. Click any area in your results to see every check and how to fix it.</div></div>
  </div>
</section>

<section id="results">
  <div class="glass rhead">
    <div><div class="label" id="rDate"></div><h2 id="rUrl"></h2></div>
    <div class="acts">
      <button class="btn ghost" id="dlPdf">Download PDF</button>
      <button class="btn ghost" id="dlReport">HTML</button>
      <button class="btn ghost" id="dlJson">JSON</button>
      <button class="btn lime" id="newAudit">New audit</button>
    </div>
  </div>
  <div class="bento">
    <div class="dark gauge c4" id="gaugeCard"></div>
    <div class="glass card c8"><div class="label">Executive summary</div><div class="summary" id="summary"></div><div class="metrics" id="metrics"></div></div>
  </div>
  <div class="grid10" id="grid10"></div>
  <div class="bento">
    <div class="glass card c7 plan"><div class="label">Action plan · fix first</div><ol id="plan"></ol></div>
    <div class="dark card c5"><div class="label">Quick wins</div><div class="wins" id="wins"></div>
      <div class="label" style="margin-top:22px">Re-audit</div><p style="font-size:14px;color:#d6d1c7;margin:8px 0 0" id="reaudit"></p></div>
    <div class="glass card c12" id="emailCard"><div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap"><div class="label">Outreach email draft</div><button class="btn ghost" id="copyEmail">Copy email</button></div><pre class="email" id="email"></pre></div>
  </div>
</section>

<section id="history" class="glass">
  <div class="rhead" style="border-bottom:1px solid var(--line)"><div><div class="label">Saved in this browser</div><h2>History</h2></div>
  <div class="acts"><button class="btn ghost" id="csv">Export CSV</button><button class="btn ghost" id="clear">Clear</button></div></div>
  <div id="histBody"></div>
</section>

<footer><span>Built by <a href="https://__BRAND__">__BRAND__</a></span><span>Want the fixes done for you? <a href="https://__BRAND__">Get in touch</a></span></footer>
</div>

<div class="drawer" id="drawer"><div class="panel glass" id="panel"></div></div>
<div class="modal" id="modal"><div class="box glass">
  <div class="label">Owner access</div><h2 style="margin:8px 0 4px;letter-spacing:-.02em">Access key</h2>
  <p style="font-size:14px;color:#4b4740;margin:0">Enter your <code>AUDIT_API_TOKEN</code> to remove demo limits (more pages, AI summary, no hourly cap). Stored only in this browser.</p>
  <input id="keyIn" type="password" placeholder="paste access key">
  <div style="display:flex;gap:8px;justify-content:flex-end"><button class="btn ghost" id="keyOut">Use demo mode</button><button class="btn" id="keySave">Save key</button></div>
</div></div>
<div class="toast" id="toast"></div>

<script>
const BRAND="__BRAND__", DAILY=__DAILY__, DEMO_PAGES=__DEMO_PAGES__;
const AREAS=[["Technical SEO","#ece6ff",'<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>'],
["Performance","#e3f3e6",'<path d="M4 16a8 8 0 1 1 16 0"/><path d="M12 16l4-5"/>'],
["Mobile Usability","#fdf2d3",'<rect x="7" y="2.5" width="10" height="19" rx="2"/><path d="M11 18.5h2"/>'],
["On-Page SEO","#e2eefc",'<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/>'],
["User Experience","#fde9d6",'<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>'],
["Conversion","#e2eefc",'<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>'],
["Content Quality","#fce3ed",'<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>'],
["Security","#ece6ff",'<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>'],
["Accessibility","#e3f3e6",'<circle cx="12" cy="4.5" r="2"/><path d="M5 9h14M12 9v12M8 21l4-7 4 7"/>'],
["Analytics","#fdf2d3",'<path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/>']];
const $=s=>document.querySelector(s), esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const col=s=>s>=90?"var(--ex)":s>=70?"var(--gd)":s>=50?"var(--ni)":s>=30?"var(--po)":"var(--cr)";
const ls={get:(k,d)=>{try{return JSON.parse(localStorage.getItem(k))??d}catch(e){return d}},set:(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
// tiny IndexedDB store for full reports
const idb=(()=>{let p;const db=()=>p||(p=new Promise((res,rej)=>{const r=indexedDB.open("audits",1);r.onupgradeneeded=()=>r.result.createObjectStore("r");r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)}));
 const tx=async(m,f)=>{const d=await db();return new Promise((res,rej)=>{const t=d.transaction("r",m);const q=f(t.objectStore("r"));t.oncomplete=()=>res(q&&q.result);t.onerror=()=>rej(t.error)})};
 return{put:(k,v)=>tx("readwrite",s=>s.put(v,k)).catch(()=>{}),get:k=>tx("readonly",s=>s.get(k)).catch(()=>null),clear:()=>tx("readwrite",s=>s.clear()).catch(()=>{})}})();
let key=ls.get("auditKey",""), current=null;
function toast(t){const e=$("#toast");e.textContent=t;e.classList.add("on");setTimeout(()=>e.classList.remove("on"),2200)}

// ---- mode
function setMode(){const owner=!!key;$("#keyDot").classList.toggle("on",owner);$("#keyLbl").textContent=owner?"Owner mode":"Demo mode";
 $("#aiOpt").hidden=!owner;const sel=$("#pages");const opts=owner?[5,10,15,25]:[DEMO_PAGES];sel.innerHTML=opts.map(n=>`<option ${n==(owner?10:DEMO_PAGES)?"selected":""}>${n}</option>`).join("");sel.disabled=!owner;
 $("#modeNote").textContent=owner?"":"Demo: limited pages · 5 audits/hour";}
$("#keyBtn").onclick=()=>{$("#keyIn").value=key;$("#modal").classList.add("on");$("#keyIn").focus()};
$("#keySave").onclick=()=>{key=$("#keyIn").value.trim();ls.set("auditKey",key);setMode();$("#modal").classList.remove("on");toast(key?"Owner mode on":"Demo mode")};
$("#keyOut").onclick=()=>{key="";ls.set("auditKey","");setMode();$("#modal").classList.remove("on");toast("Demo mode")};
$("#modal").onclick=e=>{if(e.target.id==="modal")e.target.classList.remove("on")};

// ---- quota / history
const today=()=>new Date().toISOString().slice(0,10);
function hist(){return ls.get("auditHist",[])}
function refreshQuota(){const h=hist().filter(x=>x.date===today());$("#qNum").innerHTML=`${h.length}<small> / ${DAILY}</small>`;$("#qBar").style.width=Math.min(100,h.length/DAILY*100)+"%";
 $("#qAvg").textContent=h.length?Math.round(h.reduce((a,x)=>a+x.score,0)/h.length):"—"}
function renderHistory(){const h=hist();if(!h.length){$("#histBody").innerHTML='<div class="empty">No audits yet. Run one from the Audit tab.</div>';return}
 $("#histBody").innerHTML=`<table><tr><th>Website</th><th>Score</th><th>Status</th><th>Top issue</th><th>Date</th></tr>${h.map((x,i)=>`<tr class="row" data-i="${i}"><td><b>${esc(x.url.replace(/^https?:\/\//,""))}</b></td><td><span class="sp" style="background:${col(x.score)}">${x.score}</span></td><td>${esc(x.band)}</td><td style="color:#4b4740">${esc(x.top||"—")}</td><td style="font:12px var(--mono);color:var(--muted)">${esc(x.at.slice(0,16).replace("T"," "))}</td></tr>`).join("")}</table>`;
 document.querySelectorAll("tr.row").forEach(r=>r.onclick=async()=>{const x=hist()[r.dataset.i];const full=await idb.get(x.id);if(!full)return toast("Full report not stored — re-run the audit");show(full);switchTab("audit")})}
$("#csv").onclick=()=>{const h=hist();if(!h.length)return;const rows=[["url","score","band","critical","warnings","top_issue","date"],...h.map(x=>[x.url,x.score,x.band,x.crit,x.warn,x.top,x.at])];
 const csv=rows.map(r=>r.map(v=>`"${String(v??"").replace(/"/g,'""')}"`).join(",")).join("\n");dl(new Blob([csv],{type:"text/csv"}),"audits.csv")};
$("#clear").onclick=async()=>{if(!confirm("Clear all saved audits in this browser?"))return;ls.set("auditHist",[]);await idb.clear();renderHistory();refreshQuota()};
function switchTab(t){document.querySelectorAll(".tabs button").forEach(b=>b.classList.toggle("on",b.dataset.tab===t));
 $("#history").style.display=t==="history"?"block":"none";$("#hero").style.display=t==="audit"&&!current?"grid":t==="audit"?"none":"none";
 $("#results").style.display=t==="audit"&&current?"block":"none";if(t==="history")renderHistory()}
document.querySelectorAll(".tabs button").forEach(b=>b.onclick=()=>switchTab(b.dataset.tab));

// ---- side area list + loading animation
$("#areas10").innerHTML=AREAS.map((a,i)=>`<div class="ar"><em>${String(i+1).padStart(2,"0")}</em>${a[0]}</div>`).join("");
let spin;function loading(on){const box=$("#areas10");box.parentElement.classList.toggle("loading",on);clearInterval(spin);const it=[...box.children];it.forEach(x=>x.classList.remove("on"));
 if(on){let k=0;spin=setInterval(()=>{it.forEach(x=>x.classList.remove("on"));it[k++%it.length].classList.add("on")},800)}}

// ---- run
$("#f").onsubmit=async e=>{e.preventDefault();const url=$("#url").value.trim();if(!url)return;
 const go=$("#go");go.disabled=true;go.textContent="Auditing…";$("#err").textContent="";loading(true);
 try{const r=await fetch("/api/run",{method:"POST",headers:{"content-type":"application/json",...(key?{authorization:"Bearer "+key}:{})},
   body:JSON.stringify({url,pages:+$("#pages").value,ai:key?$("#ai").checked:false})});
  const data=await r.json().catch(()=>({error:"Server error ("+r.status+")"}));
  if(!r.ok||data.error){if(r.status===401){key="";ls.set("auditKey","");setMode()}throw new Error(data.error||data.detail||"Audit failed")}
  save(data);show(data)}
 catch(err){$("#err").textContent=err.message}
 finally{go.disabled=false;go.textContent="Run audit";loading(false)}};
function save(r){const id=r.url+"|"+r.audited_at;const top=(r.action_plan.prioritize[0]||{}).check||"";
 const h=[{id,url:r.url,score:r.overall_score,band:r.band.label,top,crit:r.action_plan.counts.critical,warn:r.action_plan.counts.warnings,at:r.audited_at,date:today()},...hist()].slice(0,1000);
 ls.set("auditHist",h);idb.put(id,r);refreshQuota()}

// ---- render
function gauge(s,b){const R=110,len=Math.PI*R,ticks=[...Array(41)].map((_,i)=>{const a=Math.PI*(1-i/40),x1=150+Math.cos(a)*(R+18),y1=150-Math.sin(a)*(R+18),x2=150+Math.cos(a)*(R+(i%5?24:28)),y2=150-Math.sin(a)*(R+(i%5?24:28));
 return`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${i/40*100<=s?"#d8f36a":"#3a3833"}" stroke-width="2" stroke-linecap="round"/>`}).join("");
 return`<div class="label">Overall health score</div><svg viewBox="0 0 300 170">${ticks}<path d="M40 150 A110 110 0 0 1 260 150" fill="none" stroke="#2a2925" stroke-width="16" stroke-linecap="round"/>
 <path d="M40 150 A110 110 0 0 1 260 150" fill="none" stroke="${col(s)}" stroke-width="16" stroke-linecap="round" stroke-dasharray="${len*s/100} ${len}"/>
 <text x="150" y="138" text-anchor="middle" fill="#fff" font-size="64" font-weight="800" font-family="Inter" letter-spacing="-3">${s}</text><text x="150" y="162" text-anchor="middle" fill="#8f8a80" font-size="13" font-family="JetBrains Mono">/ 100</text></svg>
 <span class="band" style="background:${col(s)};color:#fff">${esc(b.label)}</span><div style="font-size:14px;color:#bdb8ae;margin-top:10px">${esc(b.description)}</div>`}
function show(r){current=r;switchTab("audit");
 $("#rUrl").textContent=r.url.replace(/^https?:\/\//,"");$("#rDate").textContent=`Audited ${r.audited_at.slice(0,16).replace("T"," ")} UTC · ${r.pages_crawled} pages · PSI ${r.meta.psi?"on":"off"} · AI ${r.meta.ai?"on":"off"}`;
 const c=r.action_plan.counts;
 $("#gaugeCard").innerHTML=gauge(r.overall_score,r.band)+`<div class="counts"><div><b>${c.critical}</b>critical</div><div><b>${c.warnings}</b>warnings</div><div><b>${c.passed}</b>passed</div></div>`;
 $("#summary").textContent=r.summary;
 $("#metrics").innerHTML=r.areas.slice(0,10).map(a=>`<div class="metric"><div class="label">${esc(a.key_metric_label)}</div><b>${esc(a.key_metric_value)}</b></div>`).join("");
 $("#grid10").innerHTML=r.areas.map((a,i)=>{const A=AREAS[i]||["",'#eee',''];return`<div class="glass area" data-i="${i}">
  <div class="top"><div class="ic" style="background:${A[1]}"><svg viewBox="0 0 24 24">${A[2]}</svg></div><span class="label">${String(a.number).padStart(2,"0")}</span></div>
  <h3>${esc(a.name)}</h3><div class="sc" style="color:${col(a.score)}">${a.score}<small>/100</small></div>
  <div class="mini"><i style="width:${a.score}%;background:${col(a.score)}"></i></div>
  <div class="dots">${a.checks.map(ch=>`<i class="${{pass:"p",warn:"w",fail:"f"}[ch.status]||"s"}" title="${esc(ch.label)}"></i>`).join("")}</div>
  <div class="km"><span>${esc(a.key_metric_label)}</span><b>${esc(a.key_metric_value)}</b></div></div>`}).join("");
 document.querySelectorAll(".area").forEach(el=>el.onclick=()=>openArea(r.areas[el.dataset.i]));
 $("#plan").innerHTML=r.action_plan.prioritize.map(it=>`<li><b>${esc(it.check)}</b><div class="meta"><span class="tag">${esc(it.area)}</span><span class="tag">${esc(it.impact)} impact</span><span class="tag">${esc(it.effort)}</span></div><p>${esc(it.detail)}</p><p class="fix">→ ${esc(it.fix)}</p></li>`).join("")||"<li>No critical issues 🎉</li>";
 $("#wins").innerHTML=r.quick_wins.map(w=>`<div class="win ${w.status==="done"?"done":""}"><i></i><div><b>${esc(w.title)}</b>${w.status==="done"?"<small>Looks good</small>":w.items.map(x=>`<small>${esc(x)}</small>`).join("")}</div></div>`).join("");
 $("#reaudit").textContent=`Re-audit ${r.action_plan.re_audit.cadence} to track progress.`;
 $("#email").textContent=r.outreach_email;$("#emailCard").style.display=key?"block":"none";
 $("#results").scrollIntoView({behavior:"smooth"})}
function openArea(a){const st={pass:"var(--ex)",warn:"var(--ni)",fail:"var(--cr)"};
 $("#panel").innerHTML=`<div style="display:flex;justify-content:space-between;align-items:center"><span class="label">Area ${a.number} · ${esc(a.key_metric_label)}: ${esc(a.key_metric_value)}</span><button class="btn ghost" style="min-height:34px;padding:0 12px" onclick="document.getElementById('drawer').classList.remove('on')">Close</button></div>
 <h2 style="font-size:30px;letter-spacing:-.03em;margin:12px 0 4px">${esc(a.name)}</h2><div style="font-size:44px;font-weight:800;color:${col(a.score)};letter-spacing:-.04em">${a.score}<small style="font-size:16px;color:var(--muted)">/100</small></div>
 ${a.checks.map(ch=>`<div class="chk"><h4><span class="st" style="background:${st[ch.status]||"#c9c4ba"}"></span>${esc(ch.label)}<span class="tag" style="margin-left:auto">${esc(ch.status)}</span></h4><p>${esc(ch.detail)}</p>${ch.fix&&["warn","fail"].includes(ch.status)?`<p><b>Fix:</b> ${esc(ch.fix)}</p>`:""}${(ch.pages||[]).slice(0,6).map(p=>`<code>${esc(p)}</code>`).join("")}</div>`).join("")}`;
 $("#drawer").classList.add("on")}
$("#drawer").onclick=e=>{if(e.target.id==="drawer")e.target.classList.remove("on")};
document.addEventListener("keydown",e=>{if(e.key==="Escape"){$("#drawer").classList.remove("on");$("#modal").classList.remove("on")}});
$("#newAudit").onclick=()=>{current=null;switchTab("audit");$("#url").value="";$("#url").focus();window.scrollTo({top:0,behavior:"smooth"})};
$("#copyEmail").onclick=()=>{navigator.clipboard.writeText(current.outreach_email).then(()=>toast("Email copied"))};
function dl(blob,name){const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000)}
const slug=u=>u.replace(/^https?:\/\//,"").replace(/[^a-z0-9]+/gi,"-").replace(/-+$/,"");
$("#dlJson").onclick=()=>dl(new Blob([JSON.stringify(current,null,2)],{type:"application/json"}),slug(current.url)+"-audit.json");
$("#dlReport").onclick=async()=>{const b=$("#dlReport");b.disabled=true;try{const r=await fetch("/render",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(current)});
 if(!r.ok)throw 0;dl(await r.blob(),slug(current.url)+"-audit.html")}catch(e){toast("Couldn't build report")}finally{b.disabled=false}};
$("#dlPdf").onclick=async()=>{const b=$("#dlPdf");b.disabled=true;b.textContent="Preparing…";const body=JSON.stringify(current);
 try{const r=await fetch("/pdf",{method:"POST",headers:{"content-type":"application/json"},body});
  if(r.ok&&(r.headers.get("content-type")||"").includes("pdf")){dl(await r.blob(),slug(current.url)+"-audit.pdf");return}
  // fallback: print-ready page -> Save as PDF
  const w=window.open("","_blank");if(!w){toast("Allow pop-ups to save the PDF");return}
  w.document.write("<p style='font:16px Inter,sans-serif;padding:40px'>Preparing your report…</p>");
  const h=await fetch("/render?print=1",{method:"POST",headers:{"content-type":"application/json"},body});
  const html=await h.text();w.document.open();w.document.write(html);w.document.close();toast("Choose “Save as PDF” in the print dialog")}
 catch(e){toast("Couldn't create the PDF")}finally{b.disabled=false;b.textContent="Download PDF"}};
setMode();refreshQuota();
const q=new URLSearchParams(location.search).get("url");if(q){$("#url").value=q;$("#f").requestSubmit()}
</script></body></html>"""


def render_app(brand: str, daily: int, demo_pages: int) -> str:
    short = brand.split(".")[0][:18]
    return (APP_HTML.replace("__BRANDSHORT__", short).replace("__BRAND__", brand)
            .replace("__DAILY__", str(daily)).replace("__DEMO_PAGES__", str(demo_pages)))
