"""HTTP API + web app.

Run locally:  uvicorn api.index:app --reload
Endpoints:
  GET  /             web app (one URL per audit, results dashboard, history)
  POST /api/run      {"url": "...", "pages": 10, "ai": false}  -> JSON report
                     Demo mode (no key): DEMO_PAGES pages, no AI, DEMO_PER_HOUR audits/hour per visitor.
                     Owner mode (Authorization: Bearer AUDIT_API_TOKEN): up to 25 pages, AI optional, no hourly cap.
  POST /render       body = JSON report -> downloadable HTML report
  GET  /health
  POST /audit        full API for integrations (token)                -> JSON report
  GET  /report?url=  full HTML report (token)
Env: AUDIT_API_TOKEN, PSI_API_KEY, ANTHROPIC_API_KEY, AUDIT_BRAND, DEMO_PAGES (5), DEMO_PER_HOUR (5), DAILY_TARGET (200).
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
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from audit_agent.agent import run_audit
from audit_agent.report_md import to_json, to_markdown
from audit_agent.web_ui import render_app

try:
    from audit_agent.report_html import to_html, to_pdf
    HAS_HTML = True
except ImportError:
    HAS_HTML = False

app = FastAPI(title="Website Audit Agent", version="1.2.0")
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
DAILY_TARGET = int(os.getenv("DAILY_TARGET", "200"))
_hits: dict = {}


def is_owner(authorization) -> bool:
    token = os.getenv("AUDIT_API_TOKEN")
    return bool(token) and authorization == f"Bearer {token}"


def auth(authorization):
    token = os.getenv("AUDIT_API_TOKEN")
    if token and authorization != f"Bearer {token}":
        raise HTTPException(401, "Invalid or missing token")


def safe_url(url: str) -> str:
    """Only public http(s) sites — blocks localhost/private networks."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    host = urlparse(url).hostname or ""
    if os.getenv("AUDIT_ALLOW_PRIVATE") == "1":  # local testing only
        return url
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


def client_ip(request: Request) -> str:
    return (request.headers.get("x-forwarded-for") or (request.client.host if request.client else "?")).split(",")[0].strip()


# ---------------------------------------------------------------- web app
@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(render_app(BRAND, DAILY_TARGET, DEMO_PAGES))


@app.get("/demo")
def demo_redirect(url: str = ""):
    return RedirectResponse(f"/?url={url}" if url else "/")


class RunIn(BaseModel):
    url: str
    pages: int = 10
    ai: bool = False


@app.post("/api/run")
async def run(body: RunIn, request: Request, authorization: str | None = Header(None)):
    owner = is_owner(authorization)
    if authorization and not owner:
        return JSONResponse({"error": "Access key is wrong — switched back to demo mode."}, status_code=401)
    try:
        target = safe_url(body.url)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    if not owner and rate_limited(client_ip(request)):
        return JSONResponse({"error": f"Demo limit reached ({DEMO_PER_HOUR} audits per hour). Try again later."}, status_code=429)
    pages = max(1, min(body.pages, 25)) if owner else DEMO_PAGES
    try:
        r = await run_audit(target, max_pages=pages, use_psi=bool(os.getenv("PSI_API_KEY")) or not SERVERLESS,
                            use_browser=not SERVERLESS, use_ai=owner and body.ai, log=lambda *_: None)
    except Exception:
        return JSONResponse({"error": "Couldn't audit that site — it may be blocking bots or timing out."}, status_code=502)
    if not r["pages_crawled"] or not any(p["status"] == 200 for p in r["meta"].get("pages", [])):
        return JSONResponse({"error": "Couldn't load that site — check the address and try again."}, status_code=422)
    if not owner:
        r["outreach_email"] = ""
    return JSONResponse(json.loads(to_json(r)))


@app.post("/render")
async def render(request: Request, print: int = 0):
    """JSON report -> HTML report. ?print=1 opens the print dialog (Save as PDF)."""
    if not HAS_HTML:
        raise HTTPException(404, "HTML reports are not included in this edition")
    try:
        r = await request.json()
        page = to_html(r, brand=BRAND, print_mode=bool(print))
    except Exception:
        raise HTTPException(400, "Invalid report")
    return HTMLResponse(page)


@app.post("/pdf")
async def pdf(request: Request):
    """JSON report -> real PDF file. Needs Playwright + Chromium, so it's unavailable on Vercel (the app then falls back to print)."""
    if not HAS_HTML or SERVERLESS:
        raise HTTPException(501, "PDF rendering not available on this host")
    try:
        r = await request.json()
        data = await to_pdf(r, brand=BRAND)
    except ImportError:
        raise HTTPException(501, "Playwright not installed")
    except Exception as e:
        raise HTTPException(500, f"PDF failed: {e}")
    from fastapi.responses import Response
    return Response(data, media_type="application/pdf")


# ---------------------------------------------------------------- integrations (token)
class AuditIn(BaseModel):
    url: str
    pages: int = 15
    psi: bool = True
    browser: bool = not SERVERLESS
    ai: bool = True
    sender: str = os.getenv("AUDIT_SENDER", "Bright")


@app.get("/health")
def health():
    return {"ok": True, "html": HAS_HTML, "ai": bool(os.getenv("ANTHROPIC_API_KEY")),
            "psi_key": bool(os.getenv("PSI_API_KEY")), "owner_key_set": bool(os.getenv("AUDIT_API_TOKEN"))}


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
