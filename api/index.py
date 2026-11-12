"""HTTP API + public demo page.

Run locally:  uvicorn api.index:app --reload
Endpoints:
  GET  /             public demo page (URL input → limited audit, rate-limited, no AI)
  GET  /demo?url=    runs the limited demo audit, returns the HTML report
  GET  /health
  POST /audit        {"url": "...", "pages": 15, "psi": true, "browser": false, "ai": true}  -> JSON report   (token)
  GET  /report?url=  -> full HTML report                                                                    (token)
Protect the full API with AUDIT_API_TOKEN (header: Authorization: Bearer <token>, or ?token=).
Demo limits via env: DEMO_PAGES (default 5), DEMO_PER_HOUR (default 5), DEMO_ENABLED (default 1).
"""
import html
import ipaddress
import json
import os
import socket
import sys
import time
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from pydantic import BaseModel

from audit_agent.agent import run_audit
from audit_agent.report_md import to_json, to_markdown

try:
    from audit_agent.report_html import to_html
    HAS_HTML = True
except ImportError:
    HAS_HTML = False

app = FastAPI(title="Website Audit Agent", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def restore_vercel_path(request: Request, call_next):
    """Vercel rewrites every URL to /api/index; vercel.json passes the original path as ?__path=."""
    from urllib.parse import parse_qsl, urlencode
    scope = request.scope
    qs = parse_qsl(scope.get("query_string", b"").decode(), keep_blank_values=True)
    orig = next((v for k, v in qs if k == "__path"), None)
    if orig is not None:
        scope["path"] = "/" + orig.lstrip("/")
        scope["raw_path"] = scope["path"].encode()
        scope["query_string"] = urlencode([(k, v) for k, v in qs if k != "__path"]).encode()
    elif scope["path"].startswith("/api/index"):
        scope["path"] = scope["path"][len("/api/index"):] or "/"
    return await call_next(request)


SERVERLESS = bool(os.getenv("VERCEL"))  # no headless browser on Vercel
BRAND = os.getenv("AUDIT_BRAND", "brightajiboye.com")
DEMO_PAGES = int(os.getenv("DEMO_PAGES", "5"))
DEMO_PER_HOUR = int(os.getenv("DEMO_PER_HOUR", "5"))
_hits: dict[str, list[float]] = {}


def auth(authorization: str | None):
    token = os.getenv("AUDIT_API_TOKEN")
    if token and authorization != f"Bearer {token}":
        raise HTTPException(401, "Invalid or missing token")


def safe_url(url: str) -> str:
    """Only public http(s) sites — blocks localhost/private networks."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    host = urlparse(url).hostname or ""
    if not host or "." not in host:
        raise ValueError("Enter a full website address, e.g. example.com")
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                raise ValueError("That address isn't a public website.")
    except socket.gaierror:
        raise ValueError("That domain doesn't resolve — check the spelling.")
    return url


def rate_limited(ip: str) -> bool:
    now = time.time()
    hits = [t for t in _hits.get(ip, []) if now - t < 3600]
    if len(hits) >= DEMO_PER_HOUR:
        _hits[ip] = hits
        return True
    _hits[ip] = hits + [now]
    return False


class AuditIn(BaseModel):
    url: str
    pages: int = 15
    psi: bool = True
    browser: bool = not SERVERLESS
    ai: bool = True
    sender: str = os.getenv("AUDIT_SENDER", "Bright")


# ---------------------------------------------------------------- public demo
LANDING = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Free Website Audit — __BRAND__</title>
<meta name="description" content="Free website audit: technical SEO, performance, mobile, on-page SEO, UX, conversion, content, security, accessibility and analytics — scored in about a minute.">
<meta property="og:title" content="Free Website Audit"><meta property="og:description" content="Score any website across 10 core areas in about a minute.">
<style>
*{box-sizing:border-box}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;background:#f7f5f0;color:#111}
main{max-width:1000px;margin:0 auto;padding:72px 24px 48px}
h1{font-size:clamp(52px,10vw,104px);line-height:.88;font-weight:900;letter-spacing:-3px;margin:0}
.sub{font-size:clamp(18px,3vw,28px);letter-spacing:10px;color:#555;font-weight:300;margin:12px 0 8px}
.eyebrow{font-size:12px;letter-spacing:2px;text-transform:uppercase;font-weight:700;color:#333}
p.lead{font-size:18px;color:#444;max-width:560px;margin:22px 0 28px}
form{display:flex;gap:10px;background:#fff;border:1px solid #e7e3da;border-radius:16px;padding:8px;max-width:640px}
input{flex:1;border:0;font:inherit;font-size:17px;padding:14px;outline:none;background:transparent;min-width:0}
button{border:0;background:#111;color:#fff;font:inherit;font-weight:700;font-size:16px;padding:0 24px;border-radius:10px;cursor:pointer}
button:disabled{opacity:.6;cursor:wait}
.note{font-size:13px;color:#777;margin-top:10px}
.err{color:#e5484d;font-size:14px;margin-top:10px;min-height:18px}
.areas{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-top:56px}
.a{background:#fff;border:1px solid #e7e3da;border-radius:12px;padding:14px;font-size:13px;font-weight:600;display:flex;gap:10px;align-items:center;transition:.3s}
.a i{font-style:normal;width:24px;height:24px;border-radius:50%;color:#fff;display:grid;place-items:center;font-size:12px;flex:none}
.loading .a{opacity:.35}.loading .a.on{opacity:1;border-color:#111}
footer{margin-top:56px;font-size:13px;color:#777;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
footer a{color:#111}
@media(max-width:760px){.areas{grid-template-columns:repeat(2,1fr)}form{flex-direction:column}button{padding:14px}}
</style></head><body><main>
<h1>WEBSITE<br>AUDIT</h1><div class="sub">FREE CHECK</div><div class="eyebrow">Analyze · Improve · Grow</div>
<p class="lead">Enter any website and get a health score out of 100, a breakdown across 10 core areas and a prioritized action plan — in about a minute.</p>
<form id="f" action="/demo" method="get">
  <input name="url" id="url" type="text" inputmode="url" autocomplete="url" placeholder="yourwebsite.com" aria-label="Website address" required>
  <button id="go" type="submit">Audit my site</button>
</form>
<div class="err" id="err" role="alert">__ERROR__</div>
<div class="note">Demo audit: up to __PAGES__ pages. No signup. Results aren't stored.</div>
<div class="areas" id="areas"></div>
<footer><span>Built by <a href="https://__BRAND__">__BRAND__</a></span><span>Want the full audit + fixes? <a href="https://__BRAND__">Get in touch</a></span></footer>
</main><script>
const A=[["Technical SEO","#7c5cff"],["Performance","#2e9e44"],["Mobile Usability","#f5b82e"],["On-Page SEO","#2f7fe0"],["User Experience","#f28c28"],["Conversion","#2f7fe0"],["Content Quality","#e8508a"],["Security","#7c5cff"],["Accessibility","#2e9e44"],["Analytics","#f5b82e"]];
const box=document.getElementById('areas');
A.forEach(([n,c],i)=>{const d=document.createElement('div');d.className='a';d.innerHTML='<i style="background:'+c+'">'+(i+1)+'</i>'+n;box.appendChild(d)});
document.getElementById('f').addEventListener('submit',e=>{
  const b=document.getElementById('go');b.disabled=true;b.textContent='Auditing…';
  document.getElementById('err').textContent='';document.body.classList.add('loading');
  const items=[...box.children];let k=0;setInterval(()=>{items.forEach(x=>x.classList.remove('on'));items[k++%items.length].classList.add('on')},900);
});
</script></body></html>"""


def landing(error: str = "") -> HTMLResponse:
    page = LANDING.replace("__BRAND__", html.escape(BRAND)).replace("__PAGES__", str(DEMO_PAGES)).replace("__ERROR__", html.escape(error))
    return HTMLResponse(page, status_code=400 if error else 200)


@app.get("/", response_class=HTMLResponse)
def home():
    if os.getenv("DEMO_ENABLED", "1") != "1":
        return HTMLResponse("<h1>Website Audit Agent API</h1><p>See /docs.</p>")
    return landing()


@app.get("/demo", response_class=HTMLResponse)
async def demo(request: Request, url: str = Query(...)):
    if os.getenv("DEMO_ENABLED", "1") != "1":
        raise HTTPException(404)
    try:
        target = safe_url(url)
    except ValueError as e:
        return landing(str(e))
    ip = (request.headers.get("x-forwarded-for") or (request.client.host if request.client else "?")).split(",")[0].strip()
    if rate_limited(ip):
        return landing(f"Demo limit reached ({DEMO_PER_HOUR} audits per hour). Try again later.")
    try:
        r = await run_audit(target, max_pages=DEMO_PAGES, use_psi=bool(os.getenv("PSI_API_KEY")),
                            use_browser=not SERVERLESS, use_ai=False, log=lambda *_: None)
    except Exception:
        return landing("Couldn't audit that site — it may be blocking bots or timing out.")
    if not r["pages_crawled"] or r["overall_score"] == 0:
        return landing("Couldn't load that site — check the address and try again.")
    page = to_html(r, brand=BRAND) if HAS_HTML else f"<pre>{html.escape(to_markdown(r))}</pre>"
    back = ('<a href="/" style="position:fixed;top:16px;right:16px;background:#111;color:#fff;padding:10px 16px;'
            'border-radius:10px;font:600 14px Inter,system-ui,sans-serif;text-decoration:none;z-index:9">Audit another site</a>')
    return HTMLResponse(page.replace("<body>", "<body>" + back, 1))


# ---------------------------------------------------------------- protected API
@app.get("/health")
def health():
    return {"ok": True, "html": HAS_HTML, "ai": bool(os.getenv("ANTHROPIC_API_KEY")), "demo": os.getenv("DEMO_ENABLED", "1") == "1"}


@app.post("/audit")
async def audit(body: AuditIn, authorization: str | None = Header(None)):
    auth(authorization)
    r = await run_audit(body.url, max_pages=min(body.pages, 50), use_psi=body.psi, use_browser=body.browser and not SERVERLESS,
                        use_ai=body.ai, sender=body.sender, log=lambda *_: None)
    return JSONResponse(json.loads(to_json(r)))


@app.get("/report")
async def report(url: str = Query(...), pages: int = 15, token: str | None = None, authorization: str | None = Header(None)):
    auth(authorization or (f"Bearer {token}" if token else None))
    r = await run_audit(url, max_pages=min(pages, 50), use_browser=not SERVERLESS, log=lambda *_: None)
    if HAS_HTML:
        return HTMLResponse(to_html(r, brand=BRAND))
    return PlainTextResponse(to_markdown(r), media_type="text/markdown")
