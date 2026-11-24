JS = r"""
const CFG = window.__CFG__;
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const col = s => s >= 90 ? "#5fd39a" : s >= 70 ? "#a3d977" : s >= 50 ? "#f2b84b" : s >= 30 ? "#ff9f5a" : "#ff6b6b";
const host = u => { try { return new URL(u.includes("//") ? u : "https://" + u).hostname.replace(/^www\./, ""); } catch (e) { return u; } };
const ls = { get: (k, d) => { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
             set: (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
const idb = (() => { let p; const db = () => p || (p = new Promise((res, rej) => { const r = indexedDB.open("auditpilot", 1); r.onupgradeneeded = () => r.result.createObjectStore("r"); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); }));
  const tx = async (m, f) => { const d = await db(); return new Promise((res, rej) => { const t = d.transaction("r", m); const q = f(t.objectStore("r")); t.oncomplete = () => res(q && q.result); t.onerror = () => rej(t.error); }); };
  return { put: (k, v) => tx("readwrite", s => s.put(v, k)).catch(() => {}), get: k => tx("readonly", s => s.get(k)).catch(() => null), clear: () => tx("readwrite", s => s.clear()).catch(() => {}) }; })();

let plan = "free", code = ls.get("ap_code", ""), key = ls.get("ap_key", ""), current = null, prev = null, tab = "overview";

const SEO_AREAS = [["Technical SEO","crawlability, sitemap, robots, canonicals, 404s, schema"],["Performance","PageSpeed, Core Web Vitals, images, caching"],["Mobile Usability","tap targets, viewport, overflow, mobile CTA"],["On-Page SEO","titles, meta, headings, internal links, alt text"],["User Experience","navigation, CTAs, readability, friction"],["Conversion","value prop, lead capture, trust, forms"],["Content Quality","relevance, freshness, depth, keywords"],["Security","SSL, headers, vulnerable libraries, exposed files"],["Accessibility","contrast, keyboard, ARIA, screen readers"],["Analytics & Tracking","GA4, goals, pixels, heatmaps, data accuracy"]];
const AEO_AREAS = [["AI Crawler Access","GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot + live firewall test"],["AI Discoverability","llms.txt, sitemaps for AI crawlers"],["Structured Data for AI","Organization, FAQ, Article, Service schema"],["Answer-Ready Content","question headings, answer-first paragraphs, lists"],["Entity & Trust (E-E-A-T)","about, authors, profiles, reviews, consistent name"],["Freshness","dates AI can read, recent updates"],["AI-Readable Rendering","content visible without JavaScript"],["Snippet & Citation Controls","nosnippet, previews, quotable summary"],["Brand Clarity for AI","can an AI describe you correctly?"]];
const STEPS = ["Fetching homepage", "Reading robots.txt & sitemap", "Following internal links", "Checking every link for 404s", "Testing SSL, headers & exposed files",
  "Knocking as GPTBot, OAI-SearchBot, PerplexityBot…", "Looking for llms.txt & schema", "Measuring speed & rendering", "Scoring 70+ SEO checks", "Scoring 40+ AEO checks", "Writing your action plan"];

function toast(t) { const e = $("#toast"); e.textContent = t; e.classList.add("on"); clearTimeout(toast.t); toast.t = setTimeout(() => e.classList.remove("on"), 2400); }
function headers() { const h = { "content-type": "application/json" }; if (key) h.authorization = "Bearer " + key; if (code) h["x-pro-code"] = code; return h; }
const isPro = () => plan === "pro" || plan === "owner";

// ---------------------------------------------------------------- plan
function setPlan(p) {
  plan = p; const pill = $("#planPill"); pill.className = "plan " + p; $("#planLbl").textContent = CFG.plans[p].label;
  $("#unlockBtn").textContent = p === "free" ? "Unlock Pro" : p === "owner" ? "Owner" : "Pro active";
  $("#pagesChip").textContent = CFG.plans[p].max_pages + " pages · " + (p === "free" ? "free" : "AEO unlocked");
  if (current) renderResults(current, true);
}
async function verifyCode(c) {
  try { const r = await (await fetch("/api/unlock", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ code: c }) })).json(); return r.ok; } catch (e) { return false; }
}

// ---------------------------------------------------------------- views
function show(v) { $$(".view").forEach(x => x.classList.toggle("on", x.id === v)); if (v !== "landing") window.scrollTo({ top: 0, behavior: "smooth" }); if (v === "history") renderHistory(); }
$$("[data-go]").forEach(a => a.addEventListener("click", e => { if (!$("#landing").classList.contains("on")) { e.preventDefault(); show("landing"); setTimeout(() => document.querySelector(a.getAttribute("href")).scrollIntoView({ behavior: "smooth" }), 60); } }));
$$("[data-view]").forEach(a => a.addEventListener("click", e => { e.preventDefault(); show(a.dataset.view); }));
$(".logo").addEventListener("click", e => { e.preventDefault(); show("landing"); });

// ---------------------------------------------------------------- landing
function renderLanding() {
  $("#seoList").innerHTML = SEO_AREAS.map(([n, d]) => `<li><div>${n}<small>${d}</small></div></li>`).join("");
  $("#aeoList").innerHTML = AEO_AREAS.map(([n, d]) => `<li><div>${n}<small>${d}</small></div></li>`).join("");
  const P = CFG.pricing;
  $("#priceCards").innerHTML = `
   <div class="card price"><div class="ph"><span class="mlabel">Free</span><span class="tag ok">SEO</span></div><div class="amt">$0</div><p class="dim">Everything you need to fix search basics.</p>
     <ul>${P.free_features.map(f => `<li>${esc(f)}</li>`).join("")}</ul><button class="btn ghost" onclick="document.getElementById('url').focus();window.scrollTo({top:0,behavior:'smooth'})">Run a free audit</button></div>
   <div class="card price blue-edge"><div class="ph"><span class="mlabel">Pro</span><span class="tag blue">AEO</span></div><div class="amt">${esc(P.aeo_report)}<small> / report</small></div>
     <p class="dim">or ${esc(P.pro_monthly)} for unlimited audits & monitoring · ${esc(P.currency_note)}</p>
     <ul>${P.pro_features.map(f => `<li>${esc(f)}</li>`).join("")}</ul><button class="btn blue" onclick="openUnlock()">${P.checkout_url ? "Get Pro" : "Get Pro access"}</button></div>`;
  $("#yr").textContent = new Date().getFullYear();
}

// ---------------------------------------------------------------- run
let logTimer;
function startLog() {
  const box = $("#inspector"); box.classList.add("running");
  box.innerHTML = `<div class="card log" id="log"><div class="ih mlabel" style="margin-bottom:10px">Live audit · ${esc(host($("#url").value))}</div></div>`;
  let i = 0; const t0 = Date.now();
  const add = () => { if (i >= STEPS.length) return; const log = $("#log"); if (!log) return;
    log.querySelectorAll(".logline:not(.done)").forEach(l => { l.classList.add("done"); l.querySelector("b").textContent = "✓"; });
    const s = ((Date.now() - t0) / 1000).toFixed(1).padStart(4, "0");
    log.insertAdjacentHTML("beforeend", `<div class="logline"><span class="t">+${s}s</span><b>›</b><span>${STEPS[i++]}</span></div>`);
    const lines = log.querySelectorAll(".logline"); if (lines.length > 9) lines[0].remove(); };
  add(); logTimer = setInterval(add, 2600);
}
function stopLog() { clearInterval(logTimer); }

async function runAudit(url) {
  const go = $("#go"); go.disabled = true; go.innerHTML = "Auditing…"; $("#err").textContent = ""; startLog();
  try {
    const r = await fetch("/api/run", { method: "POST", headers: headers(), body: JSON.stringify({ url, pages: CFG.plans[plan].max_pages, ai: true }) });
    const data = await r.json().catch(() => ({ error: "Server error (" + r.status + ")" }));
    if (!r.ok || data.error) {
      if (data.code === "bad_code") { code = ""; ls.set("ap_code", ""); setPlan(key ? plan : "free"); }
      if (r.status === 401 && key && !data.code) { key = ""; ls.set("ap_key", ""); setPlan("free"); }
      throw new Error(data.error || data.detail || "Audit failed");
    }
    await save(data); history.replaceState(null, "", "/?url=" + encodeURIComponent(host(data.url)));
    renderResults(data); show("results");
  } catch (e) { $("#err").textContent = e.message; }
  finally { stopLog(); go.disabled = false; go.innerHTML = 'Run audit <span aria-hidden="true">→</span>'; resetInspector(); }
}
const INSPECTOR = $("#inspector").innerHTML;
function resetInspector() { const b = $("#inspector"); b.classList.remove("running"); b.innerHTML = INSPECTOR; }
$("#auditForm").addEventListener("submit", e => { e.preventDefault(); const u = $("#url").value.trim(); if (u) runAudit(u); });

// ---------------------------------------------------------------- history
const hist = () => ls.get("ap_hist", []);
async function save(r) {
  const id = r.url + "|" + r.audited_at; const top = (r.action_plan.prioritize[0] || {}).check || "";
  const row = { id, url: r.url, host: host(r.url), seo: r.overall_score, aeo: r.aeo && !r.aeo.error ? r.aeo.score : null, band: r.band.label, top, at: r.audited_at, plan: r.plan };
  ls.set("ap_hist", [row, ...hist()].slice(0, 500)); await idb.put(id, r);
}
async function findPrev(r) {
  const h = hist().filter(x => x.host === host(r.url) && x.at < r.audited_at);
  return h.length ? await idb.get(h[0].id) : null;
}
function renderHistory() {
  const h = hist();
  if (!h.length) { $("#histBody").innerHTML = `<div class="empty">No audits yet — run one from the home page.</div>`; return; }
  $("#histBody").innerHTML = `<table><tr><th>Website</th><th>SEO</th><th>AI search</th><th>Status</th><th>Top issue</th><th>Date</th></tr>${h.map((x, i) => `
    <tr class="row" data-i="${i}"><td><b>${esc(x.host)}</b></td><td><span class="pill" style="background:${col(x.seo)}">${x.seo}</span></td>
    <td>${x.aeo == null ? '<span class="dim">—</span>' : `<span class="pill" style="background:${col(x.aeo)}">${x.aeo}</span>`}</td><td>${esc(x.band)}</td>
    <td class="dim">${esc(x.top || "—")}</td><td class="mono dim" style="font-size:12px">${esc(x.at.slice(0, 16).replace("T", " "))}</td></tr>`).join("")}</table>`;
  $$("#histBody tr.row").forEach(tr => tr.onclick = async () => { const x = hist()[tr.dataset.i]; const r = await idb.get(x.id); if (!r) return toast("Full report not stored — re-run it"); renderResults(r); show("results"); });
}
$("#csv").onclick = () => { const h = hist(); if (!h.length) return; const rows = [["url", "seo_score", "aeo_score", "band", "top_issue", "date"], ...h.map(x => [x.url, x.seo, x.aeo ?? "", x.band, x.top, x.at])];
  dl(new Blob([rows.map(r => r.map(v => `"${String(v ?? "").replace(/"/g, '""')}"`).join(",")).join("\n")], { type: "text/csv" }), "auditpilot-history.csv"); };
$("#clear").onclick = async () => { if (!confirm("Clear all saved audits in this browser?")) return; ls.set("ap_hist", []); await idb.clear(); renderHistory(); };

// ---------------------------------------------------------------- results
function ring(s, color, label) {
  const C = 2 * Math.PI * 46, v = Math.max(0, Math.min(100, s || 0));
  return `<svg class="ring" viewBox="0 0 108 108" role="img" aria-label="${label} ${v} out of 100"><circle cx="54" cy="54" r="46" fill="none" stroke="rgba(244,241,234,.07)" stroke-width="8"/>
    <circle cx="54" cy="54" r="46" fill="none" stroke="${color}" stroke-width="8" stroke-linecap="round" stroke-dasharray="${C * v / 100} ${C}" transform="rotate(-90 54 54)"/>
    <text x="54" y="62" text-anchor="middle" fill="#f4f1ea" font-size="32" font-weight="500">${v}</text></svg>`;
}
const delta = (now, before) => before == null || now == null ? "" : now === before ? `<span class="delta dim">±0</span>` : `<span class="delta ${now > before ? "up" : "down"}">${now > before ? "+" : ""}${now - before}</span>`;
const aeoOk = r => r.aeo && !r.aeo.error;

async function renderResults(r, keepTab) {
  current = r; if (!keepTab) tab = "overview";
  prev = await findPrev(r);
  const pages = r.meta.pages.filter(p => p.status === 200).length;
  $("#rUrl").textContent = host(r.url);
  $("#rMeta").textContent = `Audited ${r.audited_at.slice(0, 16).replace("T", " ")} UTC · ${pages} pages · ${CFG.plans[r.plan || "free"].label} report` + (prev ? ` · compared with ${prev.audited_at.slice(0, 10)}` : "");
  const c = r.action_plan.counts, A = r.aeo || {};
  const bots = (A.bots || []).filter(b => b.role === "search"); const okBots = bots.filter(b => b.robots !== "blocked").length;
  const fw = (A.bots || []).filter(b => b.live === "blocked").length;
  $("#scores").innerHTML = `
    <div class="card sc"><div class="mlabel">SEO health ${delta(r.overall_score, prev && prev.overall_score)}</div><div class="gwrap">${ring(r.overall_score, col(r.overall_score), "SEO health")}
      <div><span class="band" style="background:${col(r.overall_score)}22;color:${col(r.overall_score)}">${esc(r.band.label)}</span><p>${esc(r.band.description)}</p></div></div></div>
    <div class="card sc ${aeoOk(r) ? "" : "dim"}"><div class="mlabel">AI search readiness ${aeoOk(r) ? delta(A.score, prev && prev.aeo && prev.aeo.score) : ""}</div>${aeoOk(r) ? `<div class="gwrap">${ring(A.score, "#8ea0ff", "AI search readiness")}
      <div><span class="band" style="background:rgba(142,160,255,.14);color:#8ea0ff">${esc(A.band.label)}</span><p>${A.locked ? `${A.issues_hidden} AI-search issues found. <a href="#" onclick="openUnlock();return false">Unlock the fixes →</a>` : "How ready the site is to be found and cited by AI assistants."}</p></div></div>` : `<p style="margin-top:14px">AEO not run.</p>`}</div>
    <div class="card sc"><div class="mlabel">Issues</div><div class="statn"><div><b class="bad">${c.critical}</b><span>critical</span></div><div><b class="mid">${c.warnings}</b><span>warnings</span></div><div><b class="okc">${c.passed}</b><span>passed</span></div></div></div>
    <div class="card sc"><div class="mlabel">AI crawlers</div><div class="statn"><div><b>${okBots}/${bots.length || 0}</b><span>search bots allowed</span></div></div>
      <p style="margin-top:10px">${fw ? `<span class="bad">${fw} blocked by firewall/CDN</span>` : bots.length ? '<span class="okc">No firewall blocks detected</span>' : ""}</p></div>`;
  const T = [["overview", "Overview"], ["seo", "SEO · 10 areas"], ["aeo", "AI search (AEO)" + (A.locked ? '<span class="tag blue">Pro</span>' : "")], ["fixes", "Fix list"], ["pages", "Pages"], ["tech", "Tech stack"]];
  if (r.outreach_email) T.push(["email", "Outreach email"]);
  $("#tabs").innerHTML = T.map(([k, n]) => `<button class="tab ${k === tab ? "on" : ""}" role="tab" aria-selected="${k === tab}" data-t="${k}">${n}</button>`).join("");
  $$("#tabs .tab").forEach(b => b.onclick = () => { tab = b.dataset.t; $$("#tabs .tab").forEach(x => { x.classList.toggle("on", x === b); x.setAttribute("aria-selected", x === b); }); renderTab(); });
  renderTab();
}

function renderTab() {
  const r = current, P = $("#panel");
  P.innerHTML = ({ overview: tOverview, seo: tSeo, aeo: tAeo, fixes: tFixes, pages: tPages, tech: tTech, email: tEmail }[tab] || tOverview)(r);
  P.querySelectorAll("[data-area]").forEach(b => b.onclick = () => { const [k, i] = b.dataset.area.split(":"); openArea(k === "seo" ? r.areas[i] : r.aeo.areas[i], k); });
  P.querySelectorAll("[data-copy]").forEach(b => b.onclick = () => { navigator.clipboard.writeText(b.closest(".code").querySelector("pre").textContent).then(() => toast("Copied")); });
  P.querySelectorAll("[data-dlfile]").forEach(b => b.onclick = () => dl(new Blob([b.closest(".code").querySelector("pre").textContent], { type: "text/plain" }), b.dataset.dlfile));
  if (tab === "fixes") bindTodos();
  if (tab === "aeo" && $("#visGo")) $("#visGo").onclick = runVisibility;
}

const tagFor = (st) => ({ pass: "ok", warn: "warn", fail: "fail" }[st] || "");
function tOverview(r) {
  const home = r.meta.pages.find(p => p.status === 200) || {}; const A = r.aeo || {};
  const aeoTop = aeoOk(r) && !A.locked ? A.areas.flatMap(a => a.checks.filter(c => c.status === "fail" && c.impact === "high").map(c => ({ ...c, area: a.name }))).slice(0, 3) : [];
  return `<div class="split"><div class="card panel2"><div class="mlabel">Executive summary</div><div class="summary">${esc(r.summary)}</div>
      <div class="kv">${r.areas.slice(0, 8).map(a => `<div><span class="mlabel">${esc(a.key_metric_label)}</span><b>${esc(a.key_metric_value)}</b></div>`).join("")}</div></div>
    <div class="card panel2"><div class="mlabel">How Google shows you</div><div class="serp"><div class="u">${esc(host(r.url))} › </div><div class="t">${esc(home.title || "(no title)")}</div><div class="d">${esc(home.desc || "No meta description — Google will pick random text from the page.")}</div></div>
      <div class="mlabel" style="margin-top:18px">How AI would describe you</div>${A.ai && A.ai.ai_description ? `<p class="summary">${esc(A.ai.ai_description)}</p>` :
        A.locked ? `<p class="dim" style="margin:8px 0 0">Pro shows how ChatGPT-style assistants would describe this business, and what facts they can't find. <a href="#" onclick="openUnlock();return false">Unlock →</a></p>` : `<p class="dim" style="margin:8px 0 0">Run with AI enabled to see this.</p>`}</div></div>
  <div class="split"><div class="card panel2"><div class="mlabel">Fix first</div><ol class="prio">${[...aeoTop.map(c => ({ check: c.label, area: c.area, impact: c.impact, effort: c.effort, detail: c.detail, fix: c.fix })), ...r.action_plan.prioritize].slice(0, 8).map((it, i) => `
      <li><span class="n">${String(i + 1).padStart(2, "0")}</span><div><b>${esc(it.check)}</b><div class="meta"><span class="tag">${esc(it.area)}</span><span class="tag ${it.impact === "high" ? "fail" : ""}">${esc(it.impact)} impact</span><span class="tag">${esc(it.effort)}</span></div>
      <p>${esc(it.detail)}</p><p class="fx">→ ${esc(it.fix)}</p></div></li>`).join("") || "<li>No critical issues.</li>"}</ol></div>
    <div><div class="card panel2"><div class="mlabel">Quick wins</div><ol class="prio">${r.quick_wins.map((w, i) => `<li><span class="n">${w.status === "done" ? '<span class="okc">✓</span>' : "○"}</span><div><b>${esc(w.title)}</b>${w.status === "done" ? '<p class="okc">Looks good</p>' : w.items.slice(0, 2).map(x => `<p>${esc(x)}</p>`).join("")}</div></li>`).join("")}</ol></div>
    ${plan === "owner" ? "" : `<div class="card upsell" style="margin-top:14px;display:block"><div class="mlabel">Done-for-you</div><h3>Want this fixed for you?</h3><p>Get a quote to fix the issues in this report — SEO and AI search.</p><button class="btn light" style="margin-top:14px" onclick="openLead('fix')">Get a quote</button></div>`}</div></div>`;
}

function areaCard(a, k, i, locked) {
  const dots = a.checks.map(c => `<i class="${locked && c.locked ? (c.status === "pass" ? "p" : c.status === "info" || c.status === "skip" ? "s0" : "l") : ({ pass: "p", warn: "w", fail: "f" }[c.status] || "s0")}" title="${esc(c.label)}"></i>`).join("");
  return `<button class="card area" data-area="${k}:${i}"><div class="mlabel">${String(a.number).padStart(2, "0")} · ${esc(a.key_metric_label)}</div><h4>${esc(a.name)}</h4>
    <div class="s" style="color:${k === "aeo" ? "#8ea0ff" : col(a.score)}">${a.score}<small>/100</small></div><div class="bar2"><i style="width:${a.score}%;background:${k === "aeo" ? "#8ea0ff" : col(a.score)}"></i></div>
    <div class="dots">${dots}</div><div class="km"><span>${esc(a.key_metric_label)}</span><b>${esc(a.key_metric_value)}</b></div></button>`;
}
const tSeo = r => `<div class="grid">${r.areas.map((a, i) => areaCard(a, "seo", i)).join("")}</div>`;

function botsTable(A) {
  return `<div class="card tablewrap" style="margin-bottom:14px"><table><tr><th>Crawler</th><th>Company</th><th>Role</th><th>Powers</th><th>robots.txt</th><th>Live request</th></tr>${A.bots.map(b => `
    <tr><td><b>${esc(b.bot)}</b></td><td class="dim">${esc(b.company)}</td><td><span class="tag ${b.role === "search" ? "blue" : b.role === "user" ? "ok" : ""}">${esc(b.role_label)}</span></td><td class="dim">${esc(b.engine)}</td>
    <td><span class="st"><i style="background:${b.robots === "blocked" ? (b.role === "training" ? "#f2b84b" : "#ff6b6b") : "#5fd39a"}"></i>${esc(b.robots)}</span></td>
    <td>${b.live == null ? '<span class="dim">—</span>' : `<span class="st"><i style="background:${b.live === "blocked" ? "#ff6b6b" : "#5fd39a"}"></i>${esc(b.live)}</span>`}</td></tr>`).join("")}</table></div>`;
}

function tAeo(r) {
  const A = r.aeo;
  if (!A || A.error) return `<div class="card panel2">AEO audit unavailable${A && A.error ? ": " + esc(A.error) : ""}.</div>`;
  const P = CFG.pricing;
  if (A.locked) {
    return `<div class="card upsell"><div><div class="mlabel">AI search readiness · ${A.score}/100</div><h3>${A.issues_hidden} issues are stopping AI from citing ${esc(host(r.url))}.</h3>
      <p>Unlock the full AEO audit: what each issue is, how to fix it, ready-to-paste llms.txt & schema, and a live test of whether ChatGPT-style answer engines already cite you.</p></div>
      <div style="text-align:right"><div class="big" style="font-size:44px">${esc(P.aeo_report)}</div><div class="mlabel" style="margin:4px 0 12px">per report · or ${esc(P.pro_monthly)}</div><button class="btn blue" onclick="openUnlock()">Unlock Pro</button></div></div>
      <div class="mlabel" style="margin:20px 0 10px">Who can reach your site (free preview)</div>${botsTable(A)}
      <div class="grid">${A.areas.map((a, i) => areaCard(a, "aeo", i, true)).join("")}</div>
      <div class="mlabel" style="margin:20px 0 10px">Ready-to-paste fixes (Pro)</div>
      <div class="grid g3">${Object.values(A.fixes || {}).map(f => `<div class="card fixc lock"><b>${esc(f.title)}</b><div class="code blur"><pre>{ "generated": "for ${esc(host(r.url))}", … }</pre></div></div>`).join("")}</div>`;
  }
  const ai = A.ai || {};
  const qs = (A.visibility && A.visibility.questions) || ai.buyer_questions || [];
  return `${ai.ai_description || (ai.missing || []).length ? `<div class="split"><div class="card panel2"><div class="mlabel">How an AI assistant would describe ${esc(A.brand)}</div><p class="summary">${esc(ai.ai_description || "—")}</p></div>
      <div class="card panel2"><div class="mlabel">Facts AI can't find on your site</div>${(ai.missing || []).length ? `<ol class="prio">${ai.missing.map((m, i) => `<li><span class="n">${String(i + 1).padStart(2, "0")}</span><div>${esc(m)}</div></li>`).join("")}</ol>` : '<p class="okc">Nothing important missing.</p>'}</div></div>` : ""}
    <div class="mlabel" style="margin:6px 0 10px">AI crawler access · robots.txt + live requests</div>${botsTable(A)}
    <div class="grid">${A.areas.map((a, i) => areaCard(a, "aeo", i)).join("")}</div>
    <div class="card panel2" style="margin-top:14px" id="visCard"><div class="mlabel">AI answer visibility test</div><h3>Do AI answer engines cite you today?</h3>
      <p class="dim" style="margin:0 0 10px">We ask real answer engines the questions your buyers ask, then check whether ${esc(host(r.url))} is cited or mentioned. Edit the questions (one per line).</p>
      ${CFG.engines.length ? `<textarea id="visQ" rows="5">${esc(qs.join("\n"))}</textarea>
      <div style="display:flex;gap:14px;align-items:center;margin-top:12px;flex-wrap:wrap">${CFG.engines.map(e => `<label class="st" style="font-size:13px"><input type="checkbox" class="visE" value="${e}" checked> ${e === "claude" ? "Claude + web search" : "Perplexity"}</label>`).join("")}
      <button class="btn light sm" id="visGo" style="margin-left:auto">Run visibility test</button></div><div id="visOut">${A.visibility ? visHtml(A.visibility) : ""}</div>`
      : `<p class="mid">Not configured: add ANTHROPIC_API_KEY (Claude web search) and/or PERPLEXITY_API_KEY to your environment variables.</p>`}</div>
    <div class="mlabel" style="margin:22px 0 10px">Ready-to-paste fixes · generated from your site</div>
    ${Object.entries(A.fixes || {}).map(([k, f]) => `<div class="card fixc"><div class="ph" style="margin:0"><b>${esc(f.title)}</b><span class="tag">${esc(f.file)}</span></div><p>${esc(f.how)}</p>
      <div class="code"><div class="cbtn"><button class="btn ghost sm" data-copy>Copy</button><button class="btn ghost sm" data-dlfile="${k === "llms_txt" ? "llms.txt" : k === "robots" ? "robots-ai.txt" : k + ".json"}">Download</button></div><pre>${esc(f.code)}</pre></div></div>`).join("")}`;
}

function visHtml(v) {
  if (v.status !== "done") return `<p class="mid" style="margin-top:14px">${esc(v.message || (v.errors || []).join("; ") || "Visibility test failed.")}</p>`;
  return `<div class="split" style="margin-top:16px"><div><div class="sov">${v.share_of_voice}%</div><p class="dim">AI share of voice — cited or mentioned in ${v.cited + v.mentioned > 0 ? Math.round(v.share_of_voice * v.total / 100) : 0} of ${v.total} answers (${v.cited} citations, ${v.mentioned} mentions) across ${esc(v.engines.join(" & "))}.</p>
      ${v.results.map(x => x.error ? `<div class="vq"><span class="bad">${esc(x.engine)}: ${esc(x.error)}</span></div>` : `<details class="vq"><summary><span class="tag ${x.cited ? "ok" : x.mentioned ? "warn" : "fail"}">${x.cited ? "cited" : x.mentioned ? "mentioned" : "absent"}</span><span class="tag">${esc(x.engine)}</span><span>${esc(x.question)}</span></summary>
      <p>${esc(x.answer)}</p>${x.sources.map(s => `<div class="src">${esc(s)}</div>`).join("")}</details>`).join("")}</div>
    <div><div class="mlabel">Who AI cites instead</div>${(v.competitors || []).map(c => `<div class="comp"><span style="width:44%;word-break:break-all">${esc(c.domain)}</span><div class="bar2"><i style="width:${Math.min(100, c.count / Math.max(1, v.total) * 100)}%;background:#8ea0ff"></i></div><span class="mono dim">${c.count}</span></div>`).join("") || '<p class="dim">No other sources cited.</p>'}</div></div>`;
}
async function runVisibility() {
  const b = $("#visGo"); const qs = $("#visQ").value.split("\n").map(x => x.trim()).filter(Boolean);
  if (!qs.length) return toast("Add at least one question");
  b.disabled = true; b.textContent = "Asking AI engines…"; $("#visOut").innerHTML = `<p class="dim" style="margin-top:14px">Asking ${qs.length} questions… this takes 20–60 seconds.</p>`;
  try {
    const r = await fetch("/api/visibility", { method: "POST", headers: headers(), body: JSON.stringify({ url: current.url, brand: current.aeo.brand, questions: qs, engines: $$(".visE:checked").map(x => x.value) }) });
    const v = await r.json(); if (!r.ok) throw new Error(v.error || "Failed");
    current.aeo.visibility = v; await idb.put(current.url + "|" + current.audited_at, current); $("#visOut").innerHTML = visHtml(v);
  } catch (e) { $("#visOut").innerHTML = `<p class="bad" style="margin-top:14px">${esc(e.message)}</p>`; }
  finally { b.disabled = false; b.textContent = "Run visibility test"; }
}

function allIssues(r) {
  const seo = r.action_plan.prioritize.concat(Object.values(r.action_plan.fix_and_optimize).flat()).filter((v, i, a) => a.findIndex(x => x.check_id === v.check_id && x.area === v.area) === i)
    .map(i => ({ id: "seo:" + i.area + ":" + i.check_id, title: i.check, area: i.area, status: i.status, impact: i.impact, effort: i.effort, detail: i.detail, fix: i.fix, prio: i.priority }));
  const aeo = aeoOk(r) && !r.aeo.locked ? r.aeo.areas.flatMap(a => a.checks.filter(c => c.status === "fail" || c.status === "warn").map(c => ({ id: "aeo:" + c.id, title: c.label, area: a.name + " (AEO)", status: c.status, impact: c.impact, effort: c.effort, detail: c.detail, fix: c.fix,
    prio: ({ high: 3, medium: 2, low: 1 }[c.impact] * (c.status === "fail" ? 1 : .5) * 10 / ({ easy: 1, medium: 2, hard: 3 }[c.effort] || 1)) }))) : [];
  return seo.concat(aeo).sort((a, b) => b.prio - a.prio);
}
function tFixes(r) {
  const items = allIssues(r), done = new Set(ls.get("ap_done:" + host(r.url), [])); const n = items.filter(i => done.has(i.id)).length;
  return `<div class="card panel2"><div class="ph" style="margin:0"><div><div class="mlabel">Fix list · ${items.length} items${r.aeo && r.aeo.locked ? " · AEO fixes locked" : ""}</div><h3 id="todoCount">${n} of ${items.length} done</h3></div>
    <button class="btn ghost sm" onclick="copyAll()">Copy as checklist</button></div><div class="prog"><i id="todoBar" style="width:${items.length ? n / items.length * 100 : 0}%"></i></div>
    <ul class="todo">${items.map(i => `<li class="${done.has(i.id) ? "done" : ""}"><input type="checkbox" data-todo="${esc(i.id)}" ${done.has(i.id) ? "checked" : ""} aria-label="Mark ${esc(i.title)} done">
      <div><b>${esc(i.title)}</b> <span class="tag ${tagFor(i.status)}">${esc(i.status)}</span> <span class="tag">${esc(i.area)}</span><p>${esc(i.detail)}</p><p style="color:#f4f1ea">→ ${esc(i.fix)}</p></div>
      <span class="tag">${esc(i.impact)} · ${esc(i.effort)}</span></li>`).join("")}</ul></div>`;
}
function bindTodos() {
  $$("[data-todo]").forEach(cb => cb.onchange = () => { const k = "ap_done:" + host(current.url); const s = new Set(ls.get(k, [])); cb.checked ? s.add(cb.dataset.todo) : s.delete(cb.dataset.todo); ls.set(k, [...s]);
    cb.closest("li").classList.toggle("done", cb.checked); const tot = $$("[data-todo]").length, n = $$("[data-todo]:checked").length; $("#todoCount").textContent = `${n} of ${tot} done`; $("#todoBar").style.width = (n / tot * 100) + "%"; });
}
window.copyAll = () => { const t = allIssues(current).map(i => `- [ ] ${i.title} (${i.area}) — ${i.fix}`).join("\n"); navigator.clipboard.writeText(t).then(() => toast("Checklist copied")); };

const tPages = r => `<div class="card tablewrap"><table><tr><th>Page</th><th>Status</th><th>Title</th><th>Meta desc</th><th>Words</th><th>H1</th><th>Img no alt</th><th>Schema</th><th>Load</th></tr>${r.meta.pages.map(p => `
  <tr><td style="max-width:260px;word-break:break-all"><a href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.url.replace(/^https?:\/\/[^/]+/, "") || "/")}</a><div class="dim" style="font-size:12px">${esc(p.title || "")}</div></td>
  <td><span class="${p.status === 200 ? "okc" : "bad"} mono">${p.status || "—"}</span></td><td class="${p.title_len >= 30 && p.title_len <= 60 ? "okc" : "mid"} mono">${p.title_len ?? "—"}</td>
  <td class="${p.desc_len >= 70 && p.desc_len <= 160 ? "okc" : "mid"} mono">${p.desc_len ?? "—"}</td><td class="mono ${p.words >= 300 ? "" : "mid"}">${p.words}</td><td class="mono ${p.h1 === 1 ? "okc" : "mid"}">${p.h1 ?? "—"}</td>
  <td class="mono ${p.noalt ? "mid" : "okc"}">${p.noalt ?? "—"}</td><td class="mono">${p.schema ?? "—"}</td><td class="mono dim">${p.ms}ms</td></tr>`).join("")}</table></div>`;

function tTech(r) {
  const g = {}; (r.tech || []).forEach(t => (g[t.category] = g[t.category] || []).push(t.name)); const cr = r.meta.crawl || {};
  return `<div class="techg">${Object.entries(g).map(([c, names]) => `<div class="card"><div class="mlabel">${esc(c)}</div><div class="chips">${names.map(n => `<span class="chip">${esc(n)}</span>`).join("")}</div></div>`).join("") || '<div class="card" style="padding:18px">No technologies detected.</div>'}
    <div class="card"><div class="mlabel">Crawl facts</div><div class="chips"><span class="chip">robots.txt: ${cr.robots ? "yes" : "no"}</span><span class="chip">sitemap URLs: ${cr.sitemap_urls ?? 0}</span><span class="chip">links checked: ${cr.links_checked ?? 0}</span><span class="chip">llms.txt: ${cr.llms_txt ? "yes" : "no"}</span></div></div></div>`;
}
const tEmail = r => `<div class="card panel2"><div class="ph" style="margin:0"><div class="mlabel">Outreach email · built from this audit</div><button class="btn ghost sm" onclick="navigator.clipboard.writeText(current.outreach_email).then(()=>toast('Email copied'))">Copy</button></div><pre class="summary" style="font-family:var(--fb)">${esc(r.outreach_email)}</pre></div>`;

// ---------------------------------------------------------------- drawer
function openArea(a, kind) {
  const st = { pass: "#5fd39a", warn: "#f2b84b", fail: "#ff6b6b" };
  $("#dpanel").innerHTML = `<div class="ph" style="margin:0"><span class="mlabel">${kind === "aeo" ? "AI search" : "SEO"} · area ${a.number} · ${esc(a.key_metric_label)}: ${esc(a.key_metric_value)}</span><button class="btn ghost sm" onclick="closeDrawer()">Close</button></div>
    <h2 style="font-size:34px;margin:14px 0 4px">${esc(a.name)}</h2><div class="big" style="color:${kind === "aeo" ? "#8ea0ff" : col(a.score)}">${a.score}<small style="font-size:16px;color:var(--grey-2)">/100</small></div>
    ${a.checks.some(c => c.locked) ? `<div class="card upsell" style="padding:18px;margin-top:16px"><p>Detail and fixes for these checks are part of Pro.</p><button class="btn blue sm" onclick="openUnlock()">Unlock</button></div>` : ""}
    ${a.checks.map(c => `<div class="chk"><h5><span class="st"><i style="background:${c.locked && c.status !== "pass" ? "#4b5160" : st[c.status] || "#2b303b"}"></i></span>${esc(c.label)}<span class="tag ${c.locked && c.status !== "pass" ? "" : tagFor(c.status)}" style="margin-left:auto">${c.locked && c.status !== "pass" ? "🔒 " + c.status : esc(c.status)}</span></h5>
      ${c.detail ? `<p>${esc(c.detail)}</p>` : ""}${c.fix && ["warn", "fail"].includes(c.status) ? `<p class="fx"><b>Fix:</b> ${esc(c.fix)}</p>` : ""}${(c.pages || []).slice(0, 8).map(p => `<code>${esc(p)}</code>`).join("")}</div>`).join("")}`;
  $("#drawer").classList.add("on"); $("#drawer").setAttribute("aria-hidden", "false");
}
window.closeDrawer = () => { $("#drawer").classList.remove("on"); $("#drawer").setAttribute("aria-hidden", "true"); };
$("#drawer").onclick = e => { if (e.target.id === "drawer") closeDrawer(); };

// ---------------------------------------------------------------- modals
function openModal(html) { $("#mbox").innerHTML = html; $("#modal").classList.add("on"); $("#modal").setAttribute("aria-hidden", "false"); const f = $("#mbox").querySelector("input,button"); f && f.focus(); }
window.closeModal = () => { $("#modal").classList.remove("on"); $("#modal").setAttribute("aria-hidden", "true"); };
$("#modal").onclick = e => { if (e.target.id === "modal") closeModal(); };
document.addEventListener("keydown", e => { if (e.key === "Escape") { closeModal(); closeDrawer(); } });

function leadForm(interest, title, note) {
  const C = CFG.contact; const wa = C.whatsapp ? `https://wa.me/${C.whatsapp.replace(/\D/g, "")}?text=${encodeURIComponent(`Hi, I ran ${current ? host(current.url) : "my site"} through ${CFG.product} and I'm interested in ${interest === "pro" ? "Pro" : "getting it fixed"}.`)}` : "";
  return `<form id="leadF"><label class="fl" for="lName">Name</label><input class="inp" id="lName" autocomplete="name">
    <label class="fl" for="lEmail">Email</label><input class="inp" id="lEmail" type="email" required autocomplete="email">
    <label class="fl" for="lUrl">Website</label><input class="inp" id="lUrl" value="${esc(current ? current.url : $("#url").value)}">
    <label class="fl" for="lMsg">Message</label><textarea id="lMsg" rows="3" placeholder="${esc(note)}"></textarea>
    <div style="display:flex;gap:10px;margin-top:16px;flex-wrap:wrap"><button class="btn light" type="submit">${esc(title)}</button>${wa ? `<a class="btn ghost" href="${wa}" target="_blank" rel="noopener">WhatsApp</a>` : ""}${C.booking ? `<a class="btn ghost" href="${esc(C.booking)}" target="_blank" rel="noopener">Book a call</a>` : ""}</div>
    <p class="dim" id="leadMsg" style="font-size:14px"></p></form>`;
}
function bindLead(interest) {
  $("#leadF").onsubmit = async e => { e.preventDefault(); const m = $("#leadMsg"); m.textContent = "Sending…";
    try { const r = await fetch("/api/lead", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name: $("#lName").value, email: $("#lEmail").value, url: $("#lUrl").value, message: $("#lMsg").value, interest,
        score: current ? current.overall_score : null, aeo_score: current && aeoOk(current) ? current.aeo.score : null }) }); const d = await r.json(); if (!d.ok) throw new Error(d.error || "Failed");
      m.className = "okc"; m.textContent = "Thanks — you'll hear back shortly."; } catch (err) { m.className = "bad"; m.textContent = err.message; } };
}
window.openUnlock = () => {
  const P = CFG.pricing;
  openModal(`<div class="ph" style="margin:0"><span class="mlabel">${plan === "free" ? "Unlock Pro" : "Your plan: " + CFG.plans[plan].label}</span><button class="btn ghost sm" type="button" onclick="closeModal()">Close</button></div>
    <h2 style="font-size:34px">Get cited by AI.</h2><p class="dim">${esc(P.aeo_report)} per report or ${esc(P.pro_monthly)} · ${esc(P.currency_note)}</p>
    <ul class="alist" style="margin-top:10px">${P.pro_features.slice(1, 7).map(f => `<li><div>${esc(f)}</div></li>`).join("")}</ul>
    ${P.checkout_url ? `<a class="btn blue" style="width:100%;margin-top:14px" href="${esc(P.checkout_url)}" target="_blank" rel="noopener">Buy Pro</a>` : ""}
    <div class="mtabs"><button class="btn ghost sm" id="mtCode" type="button">I have a code</button><button class="btn ghost sm" id="mtReq" type="button">Request access</button></div><div id="mtBody"></div>
    ${plan !== "free" ? `<button class="btn ghost sm" style="margin-top:14px" type="button" onclick="signOut()">Use free plan</button>` : ""}`);
  const codeView = () => { $("#mtBody").innerHTML = `<form id="codeF"><label class="fl" for="codeIn">Pro access code</label><input class="inp" id="codeIn" autocomplete="off" value="${esc(code)}"><button class="btn light" style="margin-top:12px;width:100%">Unlock</button><p id="codeMsg" class="bad" style="font-size:14px"></p></form>`;
    $("#codeF").onsubmit = async e => { e.preventDefault(); const c = $("#codeIn").value.trim(); if (await verifyCode(c)) { code = c; ls.set("ap_code", c); setPlan(key ? "owner" : "pro"); closeModal(); toast("Pro unlocked — re-run the audit for full AEO detail"); if (current) { $("#url").value = current.url; } } else $("#codeMsg").textContent = "That code isn't valid."; }; };
  $("#mtCode").onclick = codeView; $("#mtReq").onclick = () => { $("#mtBody").innerHTML = leadForm("pro", "Request Pro access", "Tell me about your site or agency"); bindLead("pro"); };
  codeView();
};
window.openLead = (interest) => { openModal(`<div class="ph" style="margin:0"><span class="mlabel">Done-for-you fixes</span><button class="btn ghost sm" type="button" onclick="closeModal()">Close</button></div><h2 style="font-size:32px">Get this fixed.</h2><p class="dim">Send the report and get a quote for the SEO + AI search fixes.</p>${leadForm(interest, "Request a quote", "Anything specific you want fixed?")}`); bindLead(interest); };
window.signOut = () => { code = ""; key = ""; ls.set("ap_code", ""); ls.set("ap_key", ""); setPlan("free"); closeModal(); toast("Switched to the free plan"); };
$("#unlockBtn").onclick = () => openUnlock(); $("#planPill").onclick = () => openUnlock();

function openSettings() {
  const b = ls.get("ap_brand", {}); const can = isPro(); const origin = location.origin;
  openModal(`<div class="ph" style="margin:0"><span class="mlabel">Settings</span><button class="btn ghost sm" type="button" onclick="closeModal()">Close</button></div>
    <h2 style="font-size:30px">White-label reports</h2><p class="dim">${can ? "Your brand on PDF and HTML reports." : "Pro feature — put your agency's brand on every report."}</p>
    <fieldset ${can ? "" : "disabled"} style="border:0;padding:0;margin:0;${can ? "" : "opacity:.5"}">
    <label class="fl" for="bName">Agency name</label><input class="inp" id="bName" value="${esc(b.name || "")}">
    <label class="fl" for="bLogo">Logo URL</label><input class="inp" id="bLogo" value="${esc(b.logo || "")}" placeholder="https://…/logo.png">
    <label class="fl" for="bColor">Accent colour</label><input class="inp" id="bColor" value="${esc(b.color || "#2340d9")}">
    <label class="fl" for="bContact">Footer contact line</label><input class="inp" id="bContact" value="${esc(b.contact || "")}" placeholder="hello@agency.com · +974 …">
    <button class="btn light" style="margin-top:14px" id="bSave" type="button">Save branding</button></fieldset>
    <h3 style="margin-top:26px">Embed on your website</h3><p class="dim" style="margin:0 0 8px">A small audit form for your portfolio or client sites.</p>
    <div class="code"><div class="cbtn"><button class="btn ghost sm" type="button" id="embCopy">Copy</button></div><pre id="embCode">${esc(`<iframe src="${origin}/embed" title="${CFG.product}" width="100%" height="230" style="border:0;border-radius:18px" loading="lazy"></iframe>`)}</pre></div>
    <h3 style="margin-top:26px">Owner key</h3><p class="dim" style="margin:0 0 8px">Paste your AUDIT_API_TOKEN to unlock everything with no limits on this browser.</p>
    <input class="inp" id="ownKey" type="password" value="${esc(key)}"><button class="btn ghost sm" style="margin-top:10px" id="ownSave" type="button">Save key</button>`);
  $("#embCopy").onclick = () => navigator.clipboard.writeText($("#embCode").textContent).then(() => toast("Embed code copied"));
  $("#bSave") && ($("#bSave").onclick = () => { ls.set("ap_brand", { name: $("#bName").value.trim(), logo: $("#bLogo").value.trim(), color: $("#bColor").value.trim(), contact: $("#bContact").value.trim() }); toast("Branding saved"); });
  $("#ownSave").onclick = () => { key = $("#ownKey").value.trim(); ls.set("ap_key", key); setPlan(key ? "owner" : code ? "pro" : "free"); closeModal(); toast(key ? "Owner mode on — server checks the key on each audit" : "Owner key removed"); };
}
$("#settingsLink").onclick = e => { e.preventDefault(); openSettings(); };

// ---------------------------------------------------------------- downloads
function dl(blob, name) { const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 3000); }
const slug = u => host(u).replace(/[^a-z0-9]+/gi, "-");
const body = (extra) => JSON.stringify({ report: current, branding: isPro() ? ls.get("ap_brand", null) : null, ...extra });
$("#dlJson").onclick = () => dl(new Blob([JSON.stringify(current, null, 2)], { type: "application/json" }), slug(current.url) + "-audit.json");
$("#dlHtml").onclick = async () => { try { const r = await fetch("/render", { method: "POST", headers: headers(), body: body() }); if (!r.ok) throw 0; dl(await r.blob(), slug(current.url) + "-audit.html"); } catch (e) { toast("Couldn't build the HTML report"); } };
$("#dlPdf").onclick = async () => {
  const b = $("#dlPdf"); b.disabled = true; b.textContent = "Preparing…";
  try {
    if (CFG.pdf_server) { const r = await fetch("/pdf", { method: "POST", headers: headers(), body: body() });
      if (r.ok && (r.headers.get("content-type") || "").includes("pdf")) { dl(await r.blob(), slug(current.url) + "-audit.pdf"); return; } }
    const w = window.open("", "_blank"); if (!w) { toast("Allow pop-ups to save the PDF"); return; }
    w.document.write("<p style='font:16px sans-serif;padding:40px'>Preparing your report…</p>");
    const h = await fetch("/render", { method: "POST", headers: headers(), body: body({ print: 1 }) }); w.document.open(); w.document.write(await h.text()); w.document.close(); toast("Choose “Save as PDF” in the print dialog");
  } catch (e) { toast("Couldn't create the PDF"); } finally { b.disabled = false; b.textContent = "Download PDF"; }
};
$("#reAudit").onclick = () => { $("#url").value = current.url; show("landing"); window.scrollTo({ top: 0 }); runAudit(current.url); };

// ---------------------------------------------------------------- compare
$("#cmpBtn").onclick = () => { if (!isPro()) return openUnlock(); show("compare"); $("#cmpOut").innerHTML = ""; $("#cmpUrl").focus(); };
$("#cmpForm").onsubmit = async e => {
  e.preventDefault(); const b = $("#cmpGo"); b.disabled = true; b.textContent = "Auditing…"; $("#cmpErr").textContent = "";
  try { const r = await fetch("/api/run", { method: "POST", headers: headers(), body: JSON.stringify({ url: $("#cmpUrl").value, pages: Math.min(10, CFG.plans[plan].max_pages), ai: false }) });
    const them = await r.json(); if (!r.ok || them.error) throw new Error(them.error || "Failed"); renderCompare(current, them);
  } catch (err) { $("#cmpErr").textContent = err.message; } finally { b.disabled = false; b.textContent = "Compare →"; }
};
function verdict(a, b) {
  const s = (x, y, what) => x === y ? `Level on ${what}` : x > y ? `You lead on ${what} by ${x - y}` : `They lead on ${what} by ${y - x}`;
  return s(a.overall_score, b.overall_score, "SEO") + (aeoOk(a) && aeoOk(b) ? "; " + s(a.aeo.score, b.aeo.score, "AI search").replace(/^Y|^T|^L/, c => c.toLowerCase()) : "") + ".";
}
function renderCompare(a, b) {
  const row = (label, x, y) => { const w = x == null || y == null ? "" : x > y ? "a" : y > x ? "b" : ""; return `<tr><td>${esc(label)}</td><td class="mono ${w === "a" ? "okc" : ""}">${x ?? "—"}${w === "a" ? " ●" : ""}</td><td class="mono ${w === "b" ? "okc" : ""}">${y ?? "—"}${w === "b" ? " ●" : ""}</td></tr>`; };
  const ar = (A, B) => A.map((x, i) => row(x.name, x.score, B[i] && B[i].score)).join("");
  const wins = [a.overall_score > b.overall_score, aeoOk(a) && aeoOk(b) && a.aeo.score > b.aeo.score];
  $("#cmpOut").innerHTML = `<div class="split" style="margin-top:16px"><div class="card panel2"><div class="mlabel">Verdict</div><h3>${verdict(a, b)}</h3></div>
    <div class="card panel2"><div class="mlabel">Their stack</div><div class="chips">${(b.tech || []).slice(0, 10).map(t => `<span class="chip">${esc(t.name)}</span>`).join("") || "—"}</div></div></div>
    <div class="card tablewrap"><table><tr><th>Metric</th><th>${esc(host(a.url))}</th><th>${esc(host(b.url))}</th></tr>
    ${row("SEO health", a.overall_score, b.overall_score)}${aeoOk(a) && aeoOk(b) ? row("AI search readiness", a.aeo.score, b.aeo.score) : ""}
    <tr><td colspan="3" class="mlabel">SEO areas</td></tr>${ar(a.areas, b.areas)}${aeoOk(a) && aeoOk(b) ? `<tr><td colspan="3" class="mlabel">AI search areas</td></tr>${ar(a.aeo.areas, b.aeo.areas)}` : ""}</table></div>`;
}

// ---------------------------------------------------------------- init
(async function init() {
  renderLanding();
  const q = new URLSearchParams(location.search);
  if (q.get("code")) { code = q.get("code"); ls.set("ap_code", code); }
  if (key) setPlan("owner"); else if (code) setPlan((await verifyCode(code)) ? "pro" : (ls.set("ap_code", ""), code = "", "free")); else setPlan("free");
  const u = q.get("url"); if (u) { $("#url").value = u; runAudit(u); }
})();
"""
