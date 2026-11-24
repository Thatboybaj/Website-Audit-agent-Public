"""AuditPilot HTTP API + web app.

Run locally:  uvicorn api.index:app --reload
Public
  GET  /                 web app
  GET  /embed            compact audit form for iframes (portfolio, client sites)
  GET  /api/config       plans, pricing, contact, which engines are configured
  POST /api/run          {"url", "pages", "ai"} -> report, redacted to the caller's plan
  POST /api/unlock       {"code"} -> {"plan"}
  POST /api/visibility   {"url", "brand", "questions"} -> AI answer visibility (Pro)
  POST /api/lead         {"name","email","url","message","interest"} -> forwards to LEAD_WEBHOOK_URL
  POST /render           {"report", "branding"?, "print"?} -> HTML report
  POST /pdf              {"report", "branding"?} -> PDF (needs Playwright; not on Vercel)
Owner / integrations (Authorization: Bearer AUDIT_API_TOKEN)
  POST /audit            full JSON report     GET /report?url=   HTML report     GET /health
Plans: header x-pro-code: <code from PRO_CODES> unlocks Pro; the owner token unlocks everything.
"""
import html
import ipaddress
import json
import os
import socket
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from pydantic import BaseModel

from audit_agent import plans
from audit_agent.aeo import visibility
from audit_agent.agent import run_audit
from audit_agent.report_md import to_json, to_markdown
from audit_agent.web_ui import render_app, render_embed, APP_LLMS_TXT

try:
    from audit_agent.report_html import to_html, to_pdf
    HAS_HTML = True
except ImportError:
    HAS_HTML = False

app = FastAPI(title="AuditPilot", version="2.0.0")
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


SERVERLESS = bool(os.getenv("VERCEL"))
BRAND = os.getenv("AUDIT_BRAND", "brightajiboye.com")
PRODUCT = os.getenv("PRODUCT_NAME", "AuditPilot")
DEMO_PER_HOUR = int(os.getenv("DEMO_PER_HOUR", "5"))
PRO_PER_DAY = int(os.getenv("PRO_PER_DAY", "200"))
VIS_PER_DAY = int(os.getenv("VISIBILITY_PER_DAY", "30"))


def plan_of(request: Request) -> str:
    return plans.resolve(request.headers.get("authorization"), request.headers.get("x-pro-code"))


def client_ip(request: Request) -> str:
    return (request.headers.get("x-forwarded-for") or (request.client.host if request.client else "?")).split(",")[0].strip()


def safe_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    host = urlparse(url).hostname or ""
    if os.getenv("AUDIT_ALLOW_PRIVATE") == "1":
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


def config() -> dict:
    return {"product": PRODUCT, "brand": BRAND, "plans": plans.PLANS, "pricing": plans.pricing(),
            "contact": {"whatsapp": os.getenv("CONTACT_WHATSAPP", ""), "email": os.getenv("CONTACT_EMAIL", ""),
                        "booking": os.getenv("CONTACT_BOOKING_URL", "")},
            "engines": visibility.engines_available(), "ai": bool(os.getenv("ANTHROPIC_API_KEY")),
            "psi": bool(os.getenv("PSI_API_KEY")) or not SERVERLESS, "pdf_server": HAS_HTML and not SERVERLESS,
            "browser": not SERVERLESS, "demo_per_hour": DEMO_PER_HOUR}


# ---------------------------------------------------------------- pages
@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(render_app(config()))


@app.get("/embed", response_class=HTMLResponse)
def embed():
    return HTMLResponse(render_embed(config()))


@app.get("/demo")
def demo_redirect(url: str = ""):
    return RedirectResponse(f"/?url={url}" if url else "/")


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    return "User-agent: *\nAllow: /\nDisallow: /api/\n"


@app.get("/sitemap.xml")
def sitemap(request: Request):
    base = str(request.base_url).rstrip("/")
    return Response(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{base}/</loc></url></urlset>', media_type="application/xml")


@app.get("/llms.txt", response_class=PlainTextResponse)
def llms():
    return APP_LLMS_TXT.replace("__PRODUCT__", PRODUCT).replace("__BRAND__", BRAND)


@app.get("/api/config")
def api_config():
    return config()


# ---------------------------------------------------------------- audit
class RunIn(BaseModel):
    url: str
    pages: int = 10
    ai: bool = True


@app.post("/api/run")
async def run(body: RunIn, request: Request):
    plan = plan_of(request)
    if request.headers.get("x-pro-code") and plan == "free":
        return JSONResponse({"error": "That Pro code isn't valid. Remove it to run the free audit.", "code": "bad_code"}, status_code=401)
    try:
        target = safe_url(body.url)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    ent = plans.PLANS[plan]
    if plan == "free" and plans.over_limit("free:" + client_ip(request), DEMO_PER_HOUR, 3600):
        return JSONResponse({"error": f"Free limit reached ({DEMO_PER_HOUR} audits per hour). Upgrade to Pro for more.", "code": "limit"}, status_code=429)
    if plan == "pro" and plans.over_limit("pro:" + request.headers.get("x-pro-code", ""), PRO_PER_DAY, 86400):
        return JSONResponse({"error": f"Daily Pro limit reached ({PRO_PER_DAY}).", "code": "limit"}, status_code=429)
    pages = max(1, min(body.pages, ent["max_pages"]))
    try:
        r = await run_audit(target, max_pages=pages, use_psi=bool(os.getenv("PSI_API_KEY")) or not SERVERLESS,
                            use_browser=not SERVERLESS, use_ai=ent["ai"] and body.ai, aeo=True, log=lambda *_: None)
    except Exception:
        return JSONResponse({"error": "Couldn't audit that site — it may be blocking bots or timing out."}, status_code=502)
    if not any(p["status"] == 200 for p in r["meta"].get("pages", [])):
        return JSONResponse({"error": "Couldn't load that site — check the address and try again."}, status_code=422)
    return JSONResponse(json.loads(to_json(plans.redact(r, plan))))


class UnlockIn(BaseModel):
    code: str


@app.post("/api/unlock")
def unlock(body: UnlockIn, request: Request):
    if plans.over_limit("unlock:" + client_ip(request), 10, 3600):
        return JSONResponse({"ok": False, "error": "Too many attempts. Try again later."}, status_code=429)
    plan = plans.resolve(None, body.code)
    return {"ok": plan == "pro", "plan": plan, "error": "" if plan == "pro" else "Code not recognised."}


class VisIn(BaseModel):
    url: str
    brand: str = ""
    questions: list[str] = []
    engines: list[str] = []


@app.post("/api/visibility")
async def vis(body: VisIn, request: Request):
    plan = plan_of(request)
    if not plans.PLANS[plan]["visibility"]:
        return JSONResponse({"error": "AI visibility testing is a Pro feature.", "code": "pro_required"}, status_code=402)
    if plan == "pro" and plans.over_limit("vis:" + request.headers.get("x-pro-code", ""), VIS_PER_DAY, 86400):
        return JSONResponse({"error": "Daily visibility-test limit reached."}, status_code=429)
    qs = [q for q in body.questions if q.strip()][:8]
    return await visibility.run(body.url, body.brand, qs, body.engines or None, limit=8)


class LeadIn(BaseModel):
    name: str = ""
    email: str
    url: str = ""
    message: str = ""
    interest: str = "pro"
    score: int | None = None
    aeo_score: int | None = None


@app.post("/api/lead")
async def lead(body: LeadIn, request: Request):
    if plans.over_limit("lead:" + client_ip(request), 5, 3600):
        return JSONResponse({"ok": False, "error": "Too many requests."}, status_code=429)
    if "@" not in body.email or len(body.email) > 200:
        return JSONResponse({"ok": False, "error": "Enter a valid email."}, status_code=400)
    payload = {**body.model_dump(), "source": PRODUCT, "ip": client_ip(request)}
    hook = os.getenv("LEAD_WEBHOOK_URL")
    delivered = False
    if hook:
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                delivered = (await c.post(hook, json=payload)).status_code < 300
        except Exception:
            delivered = False
    print("LEAD", json.dumps(payload))  # visible in Vercel runtime logs
    return {"ok": True, "delivered": delivered}


# ---------------------------------------------------------------- reports
def branding_for(request: Request, data: dict) -> dict | None:
    b = data.get("branding") if isinstance(data, dict) else None
    return b if b and plans.PLANS[plan_of(request)]["white_label"] else None


@app.post("/render")
async def render(request: Request, print: int = 0):
    if not HAS_HTML:
        raise HTTPException(404, "HTML reports are not included in this edition")
    try:
        data = await request.json()
        rep = data.get("report", data)
        page = to_html(rep, brand=BRAND, print_mode=bool(print or data.get("print")), branding=branding_for(request, data))
    except Exception as e:
        raise HTTPException(400, f"Invalid report: {e}")
    return HTMLResponse(page)


@app.post("/pdf")
async def pdf(request: Request):
    if not HAS_HTML or SERVERLESS:
        raise HTTPException(501, "PDF rendering not available on this host")
    try:
        data = await request.json()
        out = await to_pdf(data.get("report", data), brand=BRAND, branding=branding_for(request, data))
    except ImportError:
        raise HTTPException(501, "Playwright not installed")
    except Exception as e:
        raise HTTPException(500, f"PDF failed: {e}")
    return Response(out, media_type="application/pdf")


# ---------------------------------------------------------------- owner / integrations
def auth(authorization):
    token = os.getenv("AUDIT_API_TOKEN")
    if token and authorization != f"Bearer {token}":
        raise HTTPException(401, "Invalid or missing token")


class AuditIn(BaseModel):
    url: str
    pages: int = 15
    psi: bool = True
    browser: bool = not SERVERLESS
    ai: bool = True
    aeo: bool = True
    sender: str = os.getenv("AUDIT_SENDER", "Bright")


@app.get("/health")
def health():
    return {"ok": True, "version": app.version, "html": HAS_HTML, **{k: v for k, v in config().items() if k in ("ai", "psi", "engines", "browser")},
            "pro_codes": len(plans.pro_codes()), "owner_key_set": bool(os.getenv("AUDIT_API_TOKEN")),
            "lead_webhook": bool(os.getenv("LEAD_WEBHOOK_URL"))}


@app.post("/audit")
async def audit(body: AuditIn, authorization: str | None = Header(None)):
    auth(authorization)
    r = await run_audit(body.url, max_pages=min(body.pages, 50), use_psi=body.psi, use_browser=body.browser and not SERVERLESS,
                        use_ai=body.ai, aeo=body.aeo, sender=body.sender, log=lambda *_: None)
    return JSONResponse(json.loads(to_json(plans.redact(r, "owner"))))


@app.get("/report")
async def report(url: str = Query(...), pages: int = 15, token: str | None = None, authorization: str | None = Header(None)):
    auth(authorization or (f"Bearer {token}" if token else None))
    r = await run_audit(url, max_pages=min(pages, 50), use_browser=not SERVERLESS, log=lambda *_: None)
    if HAS_HTML:
        return HTMLResponse(to_html(plans.redact(r, "owner"), brand=BRAND))
    return PlainTextResponse(to_markdown(r), media_type="text/markdown")
