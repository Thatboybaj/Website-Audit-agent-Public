"""AI answer visibility: ask real answer engines the questions buyers ask, and check whether this site is cited.
Engines: Claude with web search (ANTHROPIC_API_KEY) and Perplexity Sonar (PERPLEXITY_API_KEY)."""
from __future__ import annotations

import asyncio
import os
import re
from collections import Counter
from urllib.parse import urlparse

import httpx

from .. import ai


def engines_available() -> list[str]:
    out = []
    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("VISIBILITY_CLAUDE", "1") == "1":
        out.append("claude")
    if os.getenv("PERPLEXITY_API_KEY"):
        out.append("perplexity")
    return out


def _host(u: str) -> str:
    h = (urlparse(u if "//" in u else "https://" + u).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


async def ask_claude(q: str) -> dict:
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic()
    msg = await client.messages.create(
        model=ai.MODEL, max_tokens=900,
        messages=[{"role": "user", "content": q + "\n\nAnswer concisely and recommend specific businesses or sources where relevant."}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}])
    text, urls = [], []
    for b in msg.content:
        d = b.model_dump() if hasattr(b, "model_dump") else dict(b)
        if d.get("type") == "text":
            text.append(d.get("text", ""))
            for c in d.get("citations") or []:
                if c.get("url"):
                    urls.append(c["url"])
        elif d.get("type") == "web_search_tool_result" and isinstance(d.get("content"), list):
            for r in d["content"]:
                if isinstance(r, dict) and r.get("url"):
                    urls.append(r["url"])
    return {"answer": " ".join(text).strip(), "sources": list(dict.fromkeys(urls))}


async def ask_perplexity(q: str) -> dict:
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post("https://api.perplexity.ai/chat/completions",
                         headers={"Authorization": f"Bearer {os.environ['PERPLEXITY_API_KEY']}"},
                         json={"model": os.getenv("PERPLEXITY_MODEL", "sonar"), "messages": [{"role": "user", "content": q}]})
        r.raise_for_status()
        d = r.json()
    urls = list(d.get("citations") or []) + [s.get("url") for s in d.get("search_results") or [] if s.get("url")]
    return {"answer": d["choices"][0]["message"]["content"], "sources": list(dict.fromkeys(u for u in urls if u))}


ASK = {"claude": ask_claude, "perplexity": ask_perplexity}


async def run(url: str, brand: str, questions: list[str], engines: list[str] | None = None, limit: int = 6) -> dict:
    engines = [e for e in (engines or engines_available()) if e in ASK]
    if not engines:
        return {"status": "not_configured", "message": "Add ANTHROPIC_API_KEY (Claude web search) and/or PERPLEXITY_API_KEY to run the AI visibility test."}
    questions = [q.strip() for q in questions if q and q.strip()][:limit]
    if not questions:
        return {"status": "no_questions", "message": "No buyer questions to test."}
    me = _host(url)
    brand_rx = re.compile(re.escape(brand.strip()), re.I) if brand and len(brand.strip()) > 2 else None
    sem = asyncio.Semaphore(4)

    async def one(engine, q):
        async with sem:
            try:
                res = await asyncio.wait_for(ASK[engine](q), timeout=70)
            except Exception as e:
                return {"engine": engine, "question": q, "error": f"{type(e).__name__}: {str(e)[:160]}"}
        hosts = [_host(s) for s in res["sources"]]
        cited = any(h == me or h.endswith("." + me) for h in hosts)
        mentioned = bool(brand_rx and brand_rx.search(res["answer"]))
        return {"engine": engine, "question": q, "cited": cited, "mentioned": mentioned,
                "sources": res["sources"][:10], "answer": res["answer"][:1200]}

    rows = await asyncio.gather(*(one(e, q) for q in questions for e in engines))
    ok = [r for r in rows if "error" not in r]
    comp = Counter(h for r in ok for h in {_host(s) for s in r["sources"]} if h and h != me and not h.endswith("." + me))
    visible = [r for r in ok if r["cited"] or r["mentioned"]]
    return {
        "status": "done" if ok else "error",
        "engines": engines,
        "questions": questions,
        "results": rows,
        "share_of_voice": round(100 * len(visible) / len(ok)) if ok else 0,
        "cited": sum(r["cited"] for r in ok),
        "mentioned": sum(r["mentioned"] for r in ok),
        "total": len(ok),
        "errors": [r["error"] for r in rows if "error" in r][:5],
        "competitors": [{"domain": d, "count": n} for d, n in comp.most_common(8)],
    }
