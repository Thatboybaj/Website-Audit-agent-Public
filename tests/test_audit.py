"""Run: pytest -q   (serves the fixture site locally and audits it — no network, no API keys needed)"""
import asyncio
import functools
import http.server
import json
import os
import threading

import pytest

from audit_agent import plans
from audit_agent.agent import run_audit

ROOT = os.path.join(os.path.dirname(__file__), "fixture_site")
os.environ["NO_PROXY"] = os.environ["no_proxy"] = "127.0.0.1,localhost"


@pytest.fixture(scope="module")
def report():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    r = asyncio.run(run_audit(url, max_pages=10, use_psi=False, use_browser=False, use_ai=False, log=lambda *a: None))
    srv.shutdown()
    return r


def ids(areas):
    return {c["id"]: c["status"] for a in areas for c in a["checks"]}


def test_seo(report):
    assert len(report["areas"]) == 10 and 0 <= report["overall_score"] <= 100
    s = ids(report["areas"])
    assert s["broken_links"] in ("warn", "fail")       # fixture has 404s
    assert s["value_prop"] == "fail"                    # H1 is "Welcome"
    assert s["vulnerabilities"] != "pass"               # jQuery 1.12.4
    assert s["utm"] == "fail"                           # internal UTM link
    assert s["soft_404"] == "pass"                      # http.server returns real 404s
    assert report["action_plan"]["prioritize"]


def test_aeo(report):
    a = report["aeo"]
    assert "error" not in a and len(a["areas"]) == 9 and 0 <= a["score"] <= 100
    s = ids(a["areas"])
    assert s["ai_search_bots"] in ("warn", "fail")       # robots.txt blocks PerplexityBot
    bots = {b["bot"]: b["robots"] for b in a["bots"]}
    assert bots["PerplexityBot"] == "blocked" and bots["GPTBot"] == "blocked" and bots["OAI-SearchBot"] == "allowed"
    assert s["llms_txt"] == "warn"                       # no llms.txt
    assert s["schema_org"] == "fail"                     # no Organization schema
    qs = [q["q"] for q in a["questions_found"]]
    assert "How much does a Framer website cost?" in qs and "How it works" not in qs
    assert {"llms_txt", "robots", "organization", "website", "faq"} <= set(a["fixes"])
    assert "User-agent: OAI-SearchBot" in a["fixes"]["robots"]["code"]


def test_free_plan_hides_paid_detail(report):
    free = plans.redact(report, "free")
    a = json.dumps(free["aeo"])
    assert free["aeo"]["locked"] and free["aeo"]["issues_hidden"] > 0
    assert "User-agent:" not in a and "acceptedAnswer" not in a and free["outreach_email"] == ""
    assert "areas" not in free["aeo"] and "score" not in free["aeo"] and "bots" not in free["aeo"]
    pro = plans.redact(report, "pro")
    assert not pro["aeo"].get("locked") and pro["aeo"]["fixes"]["robots"]["code"]


def test_tech_and_pages(report):
    names = {t["name"] for t in report["tech"]}
    assert {"jQuery", "Google Analytics 4", "Calendly"} <= names
    assert any(p.get("title_len") is not None for p in report["meta"]["pages"])


def test_visibility_scoring(monkeypatch):
    from audit_agent.aeo import visibility

    async def fake(q):
        return {"answer": "Try Acme Studio or Example Co.", "sources": ["https://www.acme.com/page", "https://other.com/x"]}
    monkeypatch.setitem(visibility.ASK, "claude", fake)
    v = asyncio.run(visibility.run("https://acme.com", "Acme Studio", ["best studio?", "who builds sites?"], engines=["claude"]))
    assert v["status"] == "done" and v["cited"] == 2 and v["share_of_voice"] == 100
    assert v["competitors"][0]["domain"] == "other.com"
