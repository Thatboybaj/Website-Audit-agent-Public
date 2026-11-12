"""HTTP API — for your lead agent, n8n/Make, Supabase or a Framer front end.

Run locally:  uvicorn api.index:app --reload
Endpoints:
  GET  /health
  POST /audit        {"url": "...", "pages": 15, "psi": true, "browser": false, "ai": true}  -> JSON report
  GET  /report?url=  -> HTML report (HTML edition) or Markdown (No-HTML edition)
Protect with AUDIT_API_TOKEN (send header: Authorization: Bearer <token>).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Header, HTTPException, Query
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

app = FastAPI(title="Website Audit Agent", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
SERVERLESS = bool(os.getenv("VERCEL"))  # no headless browser on Vercel


def auth(authorization: str | None):
    token = os.getenv("AUDIT_API_TOKEN")
    if token and authorization != f"Bearer {token}":
        raise HTTPException(401, "Invalid or missing token")


class AuditIn(BaseModel):
    url: str
    pages: int = 15
    psi: bool = True
    browser: bool = not SERVERLESS
    ai: bool = True
    sender: str = os.getenv("AUDIT_SENDER", "Bright")


@app.get("/health")
def health():
    return {"ok": True, "html": HAS_HTML, "ai": bool(os.getenv("ANTHROPIC_API_KEY"))}


@app.post("/audit")
async def audit(body: AuditIn, authorization: str | None = Header(None)):
    auth(authorization)
    r = await run_audit(body.url, max_pages=min(body.pages, 50), use_psi=body.psi, use_browser=body.browser and not SERVERLESS,
                        use_ai=body.ai, sender=body.sender, log=lambda *_: None)
    import json
    return JSONResponse(json.loads(to_json(r)))


@app.get("/report")
async def report(url: str = Query(...), pages: int = 15, token: str | None = None, authorization: str | None = Header(None)):
    auth(authorization or (f"Bearer {token}" if token else None))
    r = await run_audit(url, max_pages=min(pages, 50), use_browser=not SERVERLESS, log=lambda *_: None)
    if HAS_HTML:
        return HTMLResponse(to_html(r, brand=os.getenv("AUDIT_BRAND", "brightajiboye.com")))
    return PlainTextResponse(to_markdown(r), media_type="text/markdown")
